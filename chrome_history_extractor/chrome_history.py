import os
import csv
import click
import shutil
import smtplib
import sqlite3
import datetime
from email import encoders
from os.path import expanduser
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from terminaltables import AsciiTable
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Dict, List, Optional, Any


class ChromeHistory:
    
    HISTORY_DB: str = '~/Library/Application Support/Google/Chrome/Default/History'
    COPY_PATH: str = "~/Documents/History"
    
    def __init__(self) -> None:
        self._connection = None
        self._cursor = None
    
    def __enter__(self) -> 'ChromeHistory':
        if not self._copy_history_db():
            return None
        
        self._connection, self._cursor = self._connect_history_db()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._connection:
            self._connection.commit()
            self._connection.close()
    
    def _connect_history_db(self) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
        """ connect to history db """
        
        # open destination database
        connection = sqlite3.connect(expanduser(self.COPY_PATH))
        
        # get a data cursor to work with the database
        cursor = connection.cursor()
        
        return connection, cursor

    def _copy_history_db(self) -> None:
        """ copy history db to COPY_PATH """
        
        try:
            shutil.copy(expanduser(self.HISTORY_DB), expanduser(self.COPY_PATH))
            return True
        
        except FileNotFoundError as e:
            click.secho(f"Error copying history db: {e}", fg='red')
            return False

    def _query_chrome_history(
            self, date_from: Optional[str] = None, date_to: Optional[str] = None
        ) -> sqlite3.Cursor:
        """ list existing history in chrome """
        
        query = 'SELECT datetime(last_visit_time/1000000-11644473600, ' \
                '"unixepoch") as last_visited, url, visit_count FROM urls'
        
        if date_from and date_to:
            query += ' WHERE last_visited BETWEEN ? AND ?;'
            params = (date_from, date_to)
        else:
            params = ()
        
        return self._cursor.execute(query, params)

    def get_domains(self) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """ process history """
        
        date_to = datetime.datetime.now()
        date_from = date_to - datetime.timedelta(days=7)
        
        urls = self._query_chrome_history(
            date_from.strftime("%Y-%m-%d"), 
            date_to.strftime("%Y-%m-%d")
        )
        domains = {}
        mail_to_domains = {}
        
        for row in urls:
            url = row[1]
            visit_count = row[2]
            last_visit_time = row[0]
            
            if url.startswith('http'):
                domain = url.split('/')[2]
                if domain not in domains:
                    domains[domain] = {'count': 0, 'last_visited': None}
                domains[domain]['count'] += visit_count
                domains[domain]['last_visited'] = last_visit_time
            
            elif url.startswith('mailto:'):
                domain = url.split(':')[1]
                if domain not in mail_to_domains:
                    mail_to_domains[domain] = {'count': 0, 'last_visited': None}    
                mail_to_domains[domain]['count'] += visit_count
                mail_to_domains[domain]['last_visited'] = last_visit_time

        return domains, mail_to_domains

    def get_top_100_urls(self) -> List[Tuple[str, Dict[str, Any]]]:
        """ get top 100 urls """
        
        date_to = datetime.datetime.now()
        date_from = date_to - datetime.timedelta(days=7)
        
        urls = self._query_chrome_history(
            date_from.strftime("%Y-%m-%d"), 
            date_to.strftime("%Y-%m-%d")
        )
        _top_100_urls = {}
        
        for row in urls:
            url = row[1]
            visit_count = row[2]
            last_visit_time = row[0]
            
            if url not in _top_100_urls:
                _top_100_urls[url] = {'count': 0, 'last_visited': None} 
            
            _top_100_urls[url]['count'] += visit_count
            _top_100_urls[url]['last_visited'] = last_visit_time
        
        top_100_urls = self.sort_results({k: v for k, v in _top_100_urls.items()})
        return top_100_urls[:100]

    @staticmethod
    def sort_results(
            data: Dict[str, Dict[str, Any]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """ sort domains """
        
        return sorted(data.items(), key=lambda x: x[1]['count'], reverse=True)

    @staticmethod
    def put_in_table(data: List[Tuple[str, Dict[str, Any]]]) -> str:
        """ put in table """
        
        table: List[List[Any]] = [["URL", "Count", "Last Visited"]]
        for domain, data in data:
            table.append([domain[:150], data['count'], data['last_visited']])
        return AsciiTable(table).table

    @staticmethod
    def save_to_csv(data: List[Tuple[str, Dict[str, Any]]], filename: str) -> None:
        """ save to csv """
        
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Count", "Last Visited"])
            for domain, data in data:
                writer.writerow([domain, data['count'], data['last_visited']])

    @staticmethod
    def print_in_terminal(
            domain_tables: str, mail_to_tables: str, top_100_urls_tables: str
    ) -> None:
        """ print in terminal """
        
        click.echo(domain_tables)
        click.echo(mail_to_tables)
        click.echo(top_100_urls_tables)

    @staticmethod
    def send_email(
        smtp_host: str,
        smtp_port: int,
        username: str,
        api_key: str,
        sender_email: str,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> None:
        """
        Send an email with optional HTML body and file attachments.

        :param smtp_host: SMTP server host
        :param smtp_port: SMTP server port
        :param username: SMTP username
        :param api_key: SMTP password or API key
        :param sender_email: 'From' email address
        :param recipient_email: 'To' email address
        :param subject: Email subject
        :param body_text: Plain text email body
        :param body_html: Optional HTML version of the email body
        :param attachments: List of file paths to attach
        """
        
        # Create the container (outer) email message
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email

        # Create a plain-text and HTML alternative container
        alternative_part = MIMEMultipart("alternative")

        # Attach plain text
        alternative_part.attach(MIMEText(body_text, "plain"))

        # Attach HTML part (if provided)
        if body_html:
            alternative_part.attach(MIMEText(body_html, "html"))

        # Attach the alternative part to the main message
        msg.attach(alternative_part)

        # Attach files if any
        if attachments:
            for file_path in attachments:
                if not os.path.isfile(file_path):
                    print(f"Warning: Attachment file '{file_path}' not found. Skipping.")
                    continue

                with open(file_path, "rb") as f:
                    file_data = f.read()
                    # You can also do: `part = MIMEApplication(file_data, Name=os.path.basename(file_path))`
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file_data)

                # Encode file in ASCII characters to send by email
                encoders.encode_base64(part)

                # Add header
                filename = os.path.basename(file_path)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{filename}"'
                )

                # Attach the instance 'part' to the main message
                msg.attach(part)

        # Send the email via SMTP
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                # If your SMTP server requires TLS on port 587:
                server.starttls()

                # Log in
                server.login(username, api_key)

                # Send email
                server.sendmail(sender_email, recipient_email, msg.as_string())

            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")

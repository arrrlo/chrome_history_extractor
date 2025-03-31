import os
import click
import getpass

from chrome_history_extractor.chrome_history import ChromeHistory


@click.group()
@click.pass_context
def cli(ctx):
    click.echo()
    click.secho(f'CHROME HISTORY EXTRACTOR', fg='yellow')
    click.echo()


@cli.command()
@click.pass_context
@click.option('-h', '--smtp_host', help='SMTP host')
@click.option('-p', '--smtp_port', help='SMTP port')
@click.option('-u', '--username', help='SMTP username')
@click.option('-k', '--api_key', help='SMTP api key')
@click.option('-s', '--sender_email', help='Sender email')
@click.option('-r', '--recipient_email', help='Recipient email')
def set_cron_job(
        ctx, smtp_host, smtp_port, username, api_key, 
        sender_email, recipient_email
):
    """
    edit crontab for email sending (every Monday at 15:00)
    """

    # edit crontab
    _python = '~/chrome_history_extractor/.venv/bin/python3'
    _command = 'chrome_history_extractor extract-history ' \
               f'-h {smtp_host} ' \
               f'-p {smtp_port} ' \
               f'-u {username} ' \
               f'-k {api_key} ' \
               f'-s {sender_email} ' \
               f'-r {recipient_email}'
    os.system(f'(crontab -l 2>/dev/null; echo "0 15 * * 1 {_python} {_command} '
              '> ~/chrome_history_extractor/history.log 2>&1") | crontab -')


@cli.command()
@click.pass_context
@click.option('-h', '--smtp_host', help='SMTP host')
@click.option('-p', '--smtp_port', help='SMTP port')
@click.option('-u', '--username', help='SMTP username')
@click.option('-k', '--api_key', help='SMTP api key')
@click.option('-s', '--sender_email', help='Sender email')
@click.option('-r', '--recipient_email', help='Recipient email')
def extract_history(
        ctx, smtp_host, smtp_port, username, api_key, 
        sender_email, recipient_email
):
    with ChromeHistory() as chrome_history:
        if chrome_history is None:
            click.echo()
            return
    
        # get domains and mail to domains
        domains, mail_to_domains = chrome_history.get_domains()

        # get top 100 urls
        top_100_urls = chrome_history.get_top_100_urls()

        # sort domains
        domains = chrome_history.sort_results(domains)
        mail_to_domains = chrome_history.sort_results(mail_to_domains)

        if smtp_host and smtp_port and username and api_key and sender_email and recipient_email:
            # save to csv
            chrome_history.save_to_csv(domains, "domains.csv")
            chrome_history.save_to_csv(mail_to_domains, "mail_to_domains.csv")
            chrome_history.save_to_csv(top_100_urls, "top_100_urls.csv")

            # send to email
            chrome_history.send_email(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                username=username,
                api_key=api_key,
                sender_email=sender_email,
                recipient_email=recipient_email,
                subject=f"Chrome History for {getpass.getuser()}",
                body_text="Chrome History",
                attachments=[
                    "domains.csv",
                    "mail_to_domains.csv",
                    "top_100_urls.csv"
                ]
            )
        else:
            # # put in table
            domain_tables = chrome_history.put_in_table(domains)
            mail_to_tables = chrome_history.put_in_table(mail_to_domains)
            top_100_urls_tables = chrome_history.put_in_table(top_100_urls)

            # print in terminal
            chrome_history.print_in_terminal(domain_tables, mail_to_tables, top_100_urls_tables)
    
    click.echo()

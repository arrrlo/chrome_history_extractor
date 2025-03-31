import pytest
import sqlite3
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from chrome_history_extractor.chrome_history import ChromeHistory

@pytest.fixture
def chrome_history():
    with patch('chrome_history_extractor.chrome_history.ChromeHistory.connect_history_db') as mock_connect:
        mock_connect.return_value = (Mock(spec=sqlite3.Connection), Mock(spec=sqlite3.Cursor))
        return ChromeHistory()

@pytest.fixture
def sample_history_data():
    return [
        ('2024-03-14 10:00:00', 'https://example.com/page1', 5),
        ('2024-03-14 11:00:00', 'https://test.com/page2', 3),
        ('2024-03-14 12:00:00', 'mailto:test@example.com', 1),
    ]

def test_connect_history_db(chrome_history):
    with patch('sqlite3.connect') as mock_connect:
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        connection, cursor = chrome_history.connect_history_db()
        
        assert connection == mock_connection
        assert cursor == mock_cursor

def test_copy_history_db(chrome_history):
    with patch('shutil.copy') as mock_copy:
        chrome_history.copy_history_db()
        mock_copy.assert_called_once()

def test_query_chrome_history(chrome_history):
    chrome_history._cursor.execute.return_value = []
    date_from = '2024-03-14'
    date_to = '2024-03-15'
    
    result = chrome_history._query_chrome_history(date_from, date_to)
    
    assert chrome_history._cursor.execute.called
    # Verify the query contains the BETWEEN clause when dates are provided
    assert 'BETWEEN' in chrome_history._cursor.execute.call_args[0][0]

def test_get_domains(chrome_history, sample_history_data):
    chrome_history._query_chrome_history = Mock(return_value=sample_history_data)
    
    domains, mail_to_domains = chrome_history._get_domains()
    
    assert 'example.com' in domains
    assert 'test.com' in domains
    assert 'test@example.com' in mail_to_domains
    assert domains['example.com']['count'] == 5
    assert domains['test.com']['count'] == 3
    assert mail_to_domains['test@example.com']['count'] == 1

def test_get_top_100_urls(chrome_history, sample_history_data):
    chrome_history._query_chrome_history = Mock(return_value=sample_history_data)
    
    top_urls = chrome_history._get_top_100_urls()
    
    assert len(top_urls) <= 100
    assert top_urls[0][0] == 'https://example.com/page1'
    assert top_urls[0][1]['count'] == 5

def test_sort_results():
    test_data = {
        'domain1.com': {'count': 5, 'last_visited': '2024-03-14'},
        'domain2.com': {'count': 10, 'last_visited': '2024-03-14'},
    }
    
    sorted_results = ChromeHistory._sort_results(test_data)
    
    assert sorted_results[0][0] == 'domain2.com'
    assert sorted_results[1][0] == 'domain1.com'

def test_put_in_table():
    test_data = [
        ('domain1.com', {'count': 5, 'last_visited': '2024-03-14'}),
        ('domain2.com', {'count': 10, 'last_visited': '2024-03-14'}),
    ]
    
    table = ChromeHistory._put_in_table(test_data)
    
    assert isinstance(table, str)
    assert 'domain1.com' in table
    assert 'domain2.com' in table

def test_save_to_csv():
    test_data = [
        ('domain1.com', {'count': 5, 'last_visited': '2024-03-14'}),
        ('domain2.com', {'count': 10, 'last_visited': '2024-03-14'}),
    ]
    
    m = mock_open()
    with patch('builtins.open', m):
        ChromeHistory._save_to_csv(test_data, 'test.csv')
    
    m.assert_called_once_with('test.csv', 'w')

@patch('smtplib.SMTP')
def test_send_email(mock_smtp):
    mock_smtp_instance = Mock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
    
    ChromeHistory.send_email(
        smtp_host='test.host',
        smtp_port=587,
        username='test',
        api_key='key',
        sender_email='sender@test.com',
        recipient_email='recipient@test.com',
        subject='Test',
        body_text='Test body'
    )
    
    assert mock_smtp_instance.starttls.called
    assert mock_smtp_instance.login.called
    assert mock_smtp_instance.sendmail.called
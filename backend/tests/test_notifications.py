import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from controllers.notificationController import (
    send_whatsapp_message,
    send_payment_notifications,
    get_rejected_payments,
    get_accepted_payments
)

@pytest.mark.asyncio
@patch('controllers.notificationController._driver')
async def test_send_whatsapp_message_invalid_phone(mock_driver):
    """Test send_whatsapp_message with an invalid phone format"""
    # Phone must start with 9 and have 9 digits
    result = await send_whatsapp_message("123456789", "Test Message")
    assert result['status'] == 'error'
    assert 'teléfono inválido' in result['message']

@pytest.mark.asyncio
@patch('controllers.notificationController._driver')
@patch('controllers.notificationController.send_message')
async def test_send_whatsapp_message_success(mock_send_message, mock_driver):
    """Test send_whatsapp_message successfully sends a message when session is active"""
    # Mock driver to be present (active session)
    mock_driver.present = True
    
    # Mock send_message response
    mock_send_message.return_value = {"status": "success", "message": "Sent"}
    
    result = await send_whatsapp_message("952873813", "Test Message")
    assert result['status'] == 'success'
    mock_send_message.assert_called_once_with(mock_driver, "952873813", "Test Message")

@pytest.mark.asyncio
@patch('controllers.notificationController._driver')
@patch('controllers.notificationController.send_message')
async def test_send_payment_notifications_rejected(mock_send_message, mock_driver):
    """Test batch sending of rejected payment notifications"""
    mock_driver.present = True
    mock_send_message.return_value = {"status": "success"}
    
    payments = [
        {
            "student_name": "Patricia Jimenez",
            "parent_name": "Isabel Sanchez",
            "parent_phone": "969728039",
            "course_name": "Grupo C - Ciencias Empresariales",
            "amount": 1030.56,
            "rejection_reason": "Voucher ilegible"
        }
    ]
    
    result = await send_payment_notifications("rejected", payments)
    assert result['total'] == 1
    assert result['results'][0]['status'] == 'success'
    assert result['results'][0]['student'] == 'Patricia Jimenez'
    
    # Check that the sent message contains rejection text
    called_args = mock_send_message.call_args[0]
    sent_message = called_args[2]
    assert "PAGO RECHAZADO" in sent_message
    assert "Isabel Sanchez" in sent_message
    assert "Voucher ilegible" in sent_message

@pytest.mark.asyncio
@patch('controllers.notificationController._driver')
@patch('controllers.notificationController.send_message')
async def test_send_payment_notifications_accepted(mock_send_message, mock_driver):
    """Test batch sending of accepted payment notifications"""
    mock_driver.present = True
    mock_send_message.return_value = {"status": "success"}
    
    payments = [
        {
            "student_name": "Manuel Gomez",
            "parent_name": "Teresa Castro",
            "parent_phone": "952873813",
            "course_name": "CICLO ORDINARIO GRUPO A 26-1",
            "amount": 700.00
        }
    ]
    
    result = await send_payment_notifications("accepted", payments)
    assert result['total'] == 1
    assert result['results'][0]['status'] == 'success'
    
    # Check that the sent message contains approval text
    called_args = mock_send_message.call_args[0]
    sent_message = called_args[2]
    assert "PAGO APROBADO" in sent_message
    assert "Teresa Castro" in sent_message
    assert "700.00" in sent_message

@pytest.mark.asyncio
async def test_get_rejected_payments_db_query():
    """Test that get_rejected_payments runs the correct SQL query"""
    mock_db = AsyncMock()
    mock_db.fetch.return_value = [
        {
            "student_name": "Patricia Jimenez",
            "parent_name": "Isabel Sanchez",
            "parent_phone": "969728039",
            "amount": 1030.56,
            "rejection_reason": "Voucher ilegible",
            "course_name": "Grupo C - Ciencias Empresariales",
            "created_at": "2026-06-11"
        }
    ]
    
    result = await get_rejected_payments(mock_db)
    assert len(result) == 1
    assert result[0]['student_name'] == "Patricia Jimenez"
    
    # Verify the query was executed
    mock_db.fetch.assert_called_once()
    executed_query = mock_db.fetch.call_args[0][0]
    assert "i.rejection_reason IS NOT NULL" in executed_query
    assert "INTERVAL '30 days'" in executed_query

@pytest.mark.asyncio
async def test_get_accepted_payments_db_query():
    """Test that get_accepted_payments runs the correct SQL query"""
    mock_db = AsyncMock()
    mock_db.fetch.return_value = [
        {
            "student_name": "Manuel Gomez",
            "parent_name": "Teresa Castro",
            "parent_phone": "952873813",
            "amount": 700.00,
            "course_name": "CICLO ORDINARIO GRUPO A 26-1",
            "paid_at": "2026-06-11"
        }
    ]
    
    result = await get_accepted_payments(mock_db)
    assert len(result) == 1
    assert result[0]['student_name'] == "Manuel Gomez"
    
    # Verify the query was executed
    mock_db.fetch.assert_called_once()
    executed_query = mock_db.fetch.call_args[0][0]
    assert "i.status = 'paid'" in executed_query
    assert "e.status = 'aceptado'" in executed_query
    assert "INTERVAL '7 days'" in executed_query

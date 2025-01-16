Here is the translated document in English:

Chatbot, Machine Learning, Scraping & Parser System Documentation for Grupo huntRED®

Index
	1.	Introduction
	2.	System Architecture
	3.	Platform Integrations
	•	WhatsApp
	•	Messenger
	•	Telegram
	•	Instagram
	4.	Conversation Flow
	5.	Chat State Management
	6.	Message Sending
	7.	Error and Logs Handling
	8.	Configuration and Deployment
	9.	Testing
	10.	Maintenance

Introduction

This document outlines the architecture, functionalities, and integrations of the chatbot system for huntred.com. The chatbot is designed to interact with users across multiple messaging platforms, providing real-time assistance, profile management, job search functionalities, and more.

System Architecture

The chatbot system for huntred.com is built using Django as the main framework, leveraging Python’s asynchronous capabilities to handle multiple simultaneous requests. Key components include:
	•	Django Models: Define data structures for users, chat states, API configurations, and conversation flows.
	•	Platform Integrations: Dedicated modules to manage communication with different messaging platforms (WhatsApp, Messenger, Telegram, Instagram).
	•	Messaging Services: Reusable functions to send messages, images, buttons, and other interactive elements.
	•	ChatBotHandler: The chatbot’s core, which processes incoming messages, determines responses, and manages conversation flow.
	•	NLP Utilities: Tools for text analysis, intent detection, and sentiment analysis.

Platform Integrations

WhatsApp
	•	File: /home/amigro/app/integrations/whatsapp.py
	•	Main Functions:
	•	whatsapp_webhook: Handles webhook verification and incoming messages.
	•	send_whatsapp_response: Sends responses to the user, including interactive buttons.
	•	send_whatsapp_buttons: Sends decision buttons (Yes/No) to the user.
	•	Key Configurations:
	•	WhatsAppAPI: Model storing credentials and configurations required for WhatsApp API interactions.

Messenger
	•	File: /home/amigro/app/integrations/messenger.py
	•	Main Functions:
	•	messenger_webhook: Handles webhook verification and incoming messages.
	•	send_messenger_response: Sends responses to the user, including interactive buttons.
	•	send_messenger_buttons: Sends quick-reply buttons to the user.
	•	Key Configurations:
	•	MessengerAPI: Model storing credentials and configurations required for Messenger API interactions.

Telegram
	•	File: /home/amigro/app/integrations/telegram.py
	•	Main Functions:
	•	telegram_webhook: Handles incoming messages and webhook configurations.
	•	send_telegram_response: Sends responses to the user, including interactive buttons.
	•	send_telegram_buttons: Sends quick-reply buttons to the user.
	•	Key Configurations:
	•	TelegramAPI: Model storing credentials and configurations required for Telegram API interactions.

Instagram
	•	File: /home/amigro/app/integrations/instagram.py
	•	Main Functions:
	•	instagram_webhook: Handles webhook verification and incoming messages.
	•	send_instagram_response: Sends responses to the user, including interactive buttons.
	•	send_instagram_buttons: Sends quick-reply buttons to the user.
	•	Key Configurations:
	•	InstagramAPI: Model storing credentials and configurations required for Instagram API interactions.

Conversation Flow
	1.	Message Reception:
	•	The user sends a message via a supported platform.
	•	The corresponding webhook receives and processes the message.
	2.	Message Processing:
	•	ChatBotHandler analyzes the message using NLP tools to detect intents and entities.
	•	Based on the analysis, it determines the appropriate response and the next step in the conversation flow.
	3.	Response Sending:
	•	The response is sent to the user through the respective platform.
	•	If buttons or interactive elements are needed, they are included in the message.
	4.	Chat State Management:
	•	The conversation’s state is stored in ChatState, maintaining context between messages.

Chat State Management

The ChatState model stores relevant information about the ongoing conversation with each user, including:
	•	user_id: Unique identifier for the user on the platform.
	•	platform: Messaging platform (WhatsApp, Messenger, etc.).
	•	business_unit: Associated business unit.
	•	current_question: Current question in the conversation flow.
	•	context: Additional relevant information for the conversation.

Message Sending

Functions for sending messages (send_message, send_whatsapp_buttons, send_messenger_buttons, etc.) are designed to be reusable and handle various content types, including text, images, and interactive buttons.

Sending Interactive Buttons

Interactive buttons allow users to quickly respond via predefined options, enhancing user experience and simplifying navigation in the conversation flow.

Error and Logs Handling

The system uses the logging module to record important events, errors, and debugging information. This facilitates monitoring and troubleshooting.
	•	Log Levels:
	•	INFO: General information about system operations.
	•	DEBUG: Detailed information for debugging.
	•	WARNING: Warnings about unexpected situations that do not halt the system.
	•	ERROR: Errors that prevent a function from executing correctly.
	•	CRITICAL: Severe errors that may require immediate intervention.

Configuration and Deployment

Prerequisites
	•	Python 3.8+
	•	Django 3.2+
	•	Asynchronous Dependencies:
	•	httpx
	•	asgiref
	•	celery (for asynchronous tasks in Telegram)
	•	API Configurations: Ensure credentials and tokens for each messaging platform are available.

Configuration Steps
	1.	Rename Current Files:
	•	Before uploading new files, rename the existing ones by adding _old to preserve them.

mv /home/amigro/app/integrations/messenger.py /home/amigro/app/integrations/messenger_old.py
mv /home/amigro/app/integrations/telegram.py /home/amigro/app/integrations/telegram_old.py
mv /home/amigro/app/integrations/instagram.py /home/amigro/app/integrations/instagram_old.py


	2.	Upload New Files:
	•	Replace the old files with the newly provided ones.
	3.	Install Dependencies:
	•	Ensure all required dependencies are installed.

pip install httpx asgiref celery


	4.	Configure Webhooks:
	•	Set up webhooks on each messaging platform to point to the respective endpoints on your server.
	5.	Database Migrations:
	•	Apply migrations to ensure all models are up-to-date.

python manage.py migrate


	6.	Start the Server:
	•	Start the Django server and any Celery workers if using asynchronous tasks.

python manage.py runserver
celery -A amigro worker --loglevel=info



Testing
	1.	Webhook Verification:
	•	Ensure webhooks are correctly configured and verify without errors.
	2.	Test Message Sending:
	•	Send test messages from each platform to verify chatbot responses.
	3.	Interactive Buttons Testing:
	•	Verify that interactive buttons display correctly and handle responses properly.
	4.	Error Handling Testing:
	•	Test error scenarios, such as empty messages or API failures, to ensure the system handles them seamlessly.

Maintenance
	1.	Log Monitoring:
	•	Regularly review logs to identify and resolve issues.
	2.	Dependency Updates:
	•	Keep dependencies updated to leverage improvements and security patches.
	3.	Continuous Improvements:
	•	Add new functionalities and conversation patterns as needed by users and the business.
	4.	Data Backup:
	•	Implement backup strategies to ensure critical data is protected.

This concludes the translation of the document. Let me know if you need further adjustments or additional translations!

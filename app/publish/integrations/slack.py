import slack_sdk
from slack_sdk.errors import SlackApiError
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class SlackIntegration:
    """
    Integration for publishing content to Slack channels.
    """
    def __init__(self):
        """
        Initialize Slack client with bot token from settings.
        """
        self.client = slack_sdk.WebClient(token=settings.SLACK_BOT_TOKEN)
        logger.info("SlackIntegration initialized")

    async def publish_message(self, channel: str, text: str, blocks: list = None) -> dict:
        """
        Publish a message to a Slack channel.

        Args:
            channel (str): The Slack channel ID or name to publish to.
            text (str): The text message to publish.
            blocks (list, optional): A list of Slack blocks for rich formatting.

        Returns:
            dict: Response from Slack API.
        """
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks if blocks else None
            )
            logger.info(f"Message published to Slack channel {channel}")
            return response.data
        except SlackApiError as e:
            logger.error(f"Slack API error publishing message: {str(e)}")
            raise Exception(f"Slack API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error publishing to Slack: {str(e)}")
            raise Exception(f"Error publishing to Slack: {str(e)}")

    async def upload_file(self, channel: str, file_path: str, title: str = None, initial_comment: str = None) -> dict:
        """
        Upload a file to a Slack channel.

        Args:
            channel (str): The Slack channel ID or name to upload to.
            file_path (str): Path to the file to upload.
            title (str, optional): Title of the file.
            initial_comment (str, optional): Initial comment to accompany the file.

        Returns:
            dict: Response from Slack API.
        """
        try:
            response = await self.client.files_upload(
                channels=channel,
                file=file_path,
                title=title if title else None,
                initial_comment=initial_comment if initial_comment else None
            )
            logger.info(f"File uploaded to Slack channel {channel}: {file_path}")
            return response.data
        except SlackApiError as e:
            logger.error(f"Slack API error uploading file: {str(e)}")
            raise Exception(f"Slack API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error uploading file to Slack: {str(e)}")
            raise Exception(f"Error uploading file to Slack: {str(e)}")

    async def get_channel_list(self) -> list:
        """
        Retrieve a list of available Slack channels.

        Returns:
            list: List of channel objects.
        """
        try:
            response = await self.client.conversations_list()
            logger.info("Slack channel list retrieved")
            return response.data['channels']
        except SlackApiError as e:
            logger.error(f"Slack API error retrieving channel list: {str(e)}")
            raise Exception(f"Slack API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving Slack channel list: {str(e)}")
            raise Exception(f"Error retrieving Slack channel list: {str(e)}")

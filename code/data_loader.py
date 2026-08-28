from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"


class DataLoader:
    """
    Loads all HackerRank Orchestrate dataset files.
    """

    def __init__(self):
        self.messages = pd.read_csv(
            DATASET_DIR / "messages.csv"
        )

        self.sample_messages = pd.read_csv(
            DATASET_DIR / "sample_messages.csv"
        )

        self.users = pd.read_csv(
            DATASET_DIR / "users.csv"
        )

        self.groups = pd.read_csv(
            DATASET_DIR / "groups.csv"
        )

        self.group_members = pd.read_csv(
            DATASET_DIR / "group_members.csv"
        )

        self.business_accounts = pd.read_csv(
            DATASET_DIR / "business_accounts.csv"
        )

        self.user_business_history = pd.read_csv(
            DATASET_DIR / "user_business_history.csv"
        )

        self.message_history = pd.read_csv(
            DATASET_DIR / "message_history.csv"
        )

        self.message_events = pd.read_csv(
            DATASET_DIR / "message_events.csv"
        )

        self.images = pd.read_csv(
            DATASET_DIR / "images.csv"
        )

        self.voice_notes = pd.read_csv(
            DATASET_DIR / "voice_notes.csv"
        )

        self.daily_notification_summary = pd.read_csv(
            DATASET_DIR / "daily_notification_summary.csv"
        )

    def get_dataset_summary(self):
        """
        Return row counts for all datasets.
        """

        return {
            "messages": len(self.messages),
            "sample_messages": len(self.sample_messages),
            "users": len(self.users),
            "groups": len(self.groups),
            "group_members": len(self.group_members),
            "business_accounts": len(
                self.business_accounts
            ),
            "user_business_history": len(
                self.user_business_history
            ),
            "message_history": len(
                self.message_history
            ),
            "message_events": len(
                self.message_events
            ),
            "images": len(self.images),
            "voice_notes": len(
                self.voice_notes
            ),
            "daily_notification_summary": len(
                self.daily_notification_summary
            ),
        }
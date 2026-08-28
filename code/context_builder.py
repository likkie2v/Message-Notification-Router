import pandas as pd

from retriever import HistoryRetriever


def safe_records(df):
    """
    Convert a DataFrame to clean JSON-friendly records.
    Replaces pandas NaN values with None.
    """

    if df is None or df.empty:
        return []

    records = df.to_dict(
        orient="records"
    )

    cleaned_records = []

    for record in records:
        cleaned = {}

        for key, value in record.items():

            if pd.isna(value):
                cleaned[key] = None
            else:
                cleaned[key] = value

        cleaned_records.append(cleaned)

    return cleaned_records


class ContextBuilder:
    """
    Builds complete context for each incoming message.
    """

    def __init__(self, data):
        self.data = data
        self.history_retriever = HistoryRetriever(
            data
        )

    def get_user_context(
        self,
        user_id
    ):
        """
        Retrieve receiving user's profile.
        """

        users = self.data.users

        user = users[
            users["user_id"] == user_id
        ]

        return safe_records(user)

    def get_group_context(
        self,
        user_id,
        group_id
    ):
        """
        Retrieve group details and the user's
        membership/settings for that group.
        """

        if group_id is None or pd.isna(group_id):
            return {
                "group": [],
                "membership": []
            }

        groups = self.data.groups
        members = self.data.group_members

        group = groups[
            groups["group_id"] == group_id
        ]

        membership = members[
            (members["group_id"] == group_id)
            &
            (members["user_id"] == user_id)
        ]

        return {
            "group": safe_records(group),
            "membership": safe_records(
                membership
            )
        }

    def get_business_context(
        self,
        user_id,
        business_id
    ):
        """
        Retrieve business trust information
        and user-business relationship.
        """

        if (
            business_id is None
            or pd.isna(business_id)
        ):
            return {
                "business": [],
                "relationship": []
            }

        businesses = (
            self.data.business_accounts
        )

        history = (
            self.data.user_business_history
        )

        business = businesses[
            businesses["business_id"]
            == business_id
        ]

        relationship = history[
            (history["business_id"]
             == business_id)
            &
            (history["user_id"]
             == user_id)
        ]

        return {
            "business": safe_records(
                business
            ),
            "relationship": safe_records(
                relationship
            )
        }

    def get_notification_context(
        self,
        user_id
    ):
        """
        Retrieve notification-load history
        for the receiving user.
        """

        summary = (
            self.data.daily_notification_summary
        )

        user_summary = summary[
            summary["user_id"] == user_id
        ]

        return safe_records(
            user_summary
        )

    def build_context(
        self,
        message
    ):
        """
        Build complete structured context
        for one incoming message.
        """

        user_id = message["user_id"]

        current_message_df = pd.DataFrame(
            [message]
        )

        current_message = safe_records(
            current_message_df
        )[0]

        context = {
            "current_message":
                current_message,

            "user":
                self.get_user_context(
                    user_id
                ),

            "group_context":
                self.get_group_context(
                    user_id=user_id,
                    group_id=message.get(
                        "group_id"
                    )
                ),

            "business_context":
                self.get_business_context(
                    user_id=user_id,
                    business_id=message.get(
                        "business_id"
                    )
                ),

            "notification_summary":
                self.get_notification_context(
                    user_id
                ),

            "history":
                self.history_retriever
                .build_history_context(
                    current_message
                )
        }

        return context
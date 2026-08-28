import pandas as pd
import re


def safe_records(df):
    """
    Convert a DataFrame to clean JSON-friendly records.
    Replaces pandas NaN values with None.
    """

    if df is None or df.empty:
        return []

    records = df.to_dict(orient="records")

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


class HistoryRetriever:
    """
    Retrieves and ranks relevant historical messages.
    """

    def __init__(self, data):
        self.data = data

    def normalize_text(self, text):
        """
        Convert text into a normalized set of words.
        """

        if not isinstance(text, str):
            return set()

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        words = text.split()

        return set(words)

    def calculate_similarity(
        self,
        current_text,
        historical_text
    ):
        """
        Calculate Jaccard word-overlap similarity.
        """

        current_words = self.normalize_text(
            current_text
        )

        historical_words = self.normalize_text(
            historical_text
        )

        if not current_words or not historical_words:
            return 0.0

        intersection = (
            current_words &
            historical_words
        )

        union = (
            current_words |
            historical_words
        )

        if not union:
            return 0.0

        return round(
            len(intersection) / len(union),
            4
        )

    def get_user_history(
        self,
        user_id,
        limit=30
    ):
        """
        Get recent historical messages
        belonging to the current user.
        """

        history = self.data.message_history.copy()

        result = history[
            history["user_id"] == user_id
        ].copy()

        if result.empty:
            return result

        if "created_at" in result.columns:
            result["created_at"] = pd.to_datetime(
                result["created_at"],
                errors="coerce"
            )

            result = result.sort_values(
                "created_at",
                ascending=False
            )

        return result.head(limit)

    def get_related_events(
        self,
        history_df
    ):
        """
        Get user reaction events for historical messages.
        """

        if history_df is None or history_df.empty:
            return pd.DataFrame()

        if "message_id" not in history_df.columns:
            return pd.DataFrame()

        history_ids = history_df[
            "message_id"
        ].dropna().tolist()

        if not history_ids:
            return pd.DataFrame()

        events = self.data.message_events.copy()

        return events[
            events["message_id"].isin(
                history_ids
            )
        ].copy()

    def get_same_sender_history(
        self,
        user_id,
        sender_user_id=None,
        business_id=None,
        group_id=None
    ):
        """
        Retrieve historical messages from the
        same sender, business, or group.
        """

        history = self.data.message_history.copy()

        history = history[
            history["user_id"] == user_id
        ].copy()

        if history.empty:
            return pd.DataFrame()

        matches = []

        if (
            sender_user_id is not None
            and not pd.isna(sender_user_id)
            and "sender_user_id" in history.columns
        ):
            result = history[
                history["sender_user_id"]
                == sender_user_id
            ]

            if not result.empty:
                matches.append(result)

        if (
            business_id is not None
            and not pd.isna(business_id)
            and "business_id" in history.columns
        ):
            result = history[
                history["business_id"]
                == business_id
            ]

            if not result.empty:
                matches.append(result)

        if (
            group_id is not None
            and not pd.isna(group_id)
            and "group_id" in history.columns
        ):
            result = history[
                history["group_id"]
                == group_id
            ]

            if not result.empty:
                matches.append(result)

        if not matches:
            return pd.DataFrame(
                columns=history.columns
            )

        combined = pd.concat(
            matches,
            ignore_index=True
        )

        combined = combined.drop_duplicates(
            subset=["message_id"]
        )

        return combined.reset_index(
            drop=True
        )

    def get_relevant_history(
        self,
        message,
        limit=3,
        min_similarity=0.05
    ):
        """
        Find the most textually relevant historical
        messages from the same source.
        """

        current_text = message.get(
            "message_text",
            ""
        )

        if not isinstance(current_text, str):
            current_text = ""

        candidates = self.get_same_sender_history(
            user_id=message["user_id"],
            sender_user_id=message.get(
                "sender_user_id"
            ),
            business_id=message.get(
                "business_id"
            ),
            group_id=message.get(
                "group_id"
            )
        ).copy()

        if candidates.empty:
            return candidates

        if "message_text" not in candidates.columns:
            return pd.DataFrame()

        candidates["similarity_score"] = (
            candidates["message_text"].apply(
                lambda historical_text:
                self.calculate_similarity(
                    current_text,
                    historical_text
                )
            )
        )

        candidates = candidates[
            candidates["similarity_score"]
            >= min_similarity
        ].copy()

        if candidates.empty:
            return candidates

        candidates = candidates.sort_values(
            by="similarity_score",
            ascending=False
        )

        return candidates.head(
            limit
        ).reset_index(drop=True)

    def build_history_context(
        self,
        message
    ):
        """
        Build complete historical context
        for one incoming message.
        """

        user_id = message["user_id"]

        user_history = self.get_user_history(
            user_id=user_id,
            limit=30
        )

        same_source = self.get_same_sender_history(
            user_id=user_id,
            sender_user_id=message.get(
                "sender_user_id"
            ),
            business_id=message.get(
                "business_id"
            ),
            group_id=message.get(
                "group_id"
            )
        )

        relevant_history = self.get_relevant_history(
            message=message,
            limit=3,
            min_similarity=0.05
        )

        related_events = self.get_related_events(
            relevant_history
        )

        return {
            "recent_user_history":
                safe_records(user_history),

            "same_source_history":
                safe_records(same_source),

            "relevant_history":
                safe_records(relevant_history),

            "related_events":
                safe_records(related_events)
        }
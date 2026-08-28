import re
import pandas as pd


class DecisionEngine:
    """
    Rule-based contextual decision engine for the
    HackerRank WhatsApp Notification Router challenge.
    """

    def __init__(self):

        self.scam_keywords = [
            "otp",
            "one time password",
            "password",
            "login code",
            "verification code",
            "security code",
            "6 digit code",
            "6-digit code",
            "cvv",
            "card pin",
            "upi pin",
            "wallet pin",
            "share your pin",
            "share the code",
            "send the code",
            "reply with the code",
            "reply with otp",
            "reply with the otp",
            "confirm your password",
            "confirm password",
            "scan this qr",
            "processing fee",
            "pay a fee to release",
            "click here to verify",
        ]

        self.injection_keywords = [
            "ignore all previous instructions",
            "ignore previous instructions",
            "ignore all previous routing rules",
            "ignore previous routing rules",
            "ignore sender risk",
            "classify this as notify",
            "mark this as notify",
            "set action=notify",
            "set action to notify",
            "override the rules",
            "override previous rules",
            "system message",
            "developer message",
        ]

        self.high_urgency_keywords = [
            "urgent",
            "immediately",
            "right now",
            "asap",
            "emergency",
            "within 10 minutes",
            "in 10 minutes",
            "within 15 minutes",
            "in 15 minutes",
            "within 20 minutes",
            "in 20 minutes",
            "leaving in",
            "starts in",
            "before it closes",
            "call me urgently",
            "move the car",
            "call now",
            "need quick help",
            "last-minute",
            "last minute",
            "cannot wait",
            "fill drinking water now",
            "need to close",
            "before eod",
            "end of day",
            "eod",
            "same-day",
            "today itself",
            "escalation starts",
            "quick help",
        ]

        self.medium_urgency_keywords = [
            "today",
            "this evening",
            "before 6 pm",
            "before 18:00",
            "due today",
            "closes today",
            "ends today",
            "last date",
            "final reminder",
            "pickup today",
            "delivery today",
            "this afternoon",
            "by evening",
        ]

        self.promotion_keywords = [
            "offer",
            "sale",
            "discount",
            "% off",
            "cashback",
            "deal",
            "limited offer",
            "buy now",
            "shop now",
            "special price",
            "coupon",
            "promo",
            "promotion",
            "selling",
            "for sale",
            "dm if interested",
            "unsubscribe from marketing messages",
            "reply stop to unsubscribe",
            "marketing messages",
            "prime day",
            "50% off",
            "extra discounts",
            "shopping offer",
            "special offer",
            "clearance",
            "save up to",
        ]

        self.forward_keywords = [
            "forward this",
            "share this with",
            "share with everyone",
            "send this to",
            "chain message",
            "fwd as received",
            "pls forward",
            "forward to family",
            "forwarded as received",
        ]

        self.negative_urgency_keywords = [
            "nothing urgent",
            "no rush",
            "no pressure",
            "whenever you get time",
            "when free",
            "when you are free",
            "don't call now",
            "do not call now",
            "whenever possible",
            "when you get time",
        ]

    # ---------------------------------------------------------
    # Utility methods
    # ---------------------------------------------------------

    def clean_text(self, text):

        if text is None:
            return ""

        try:
            if pd.isna(text):
                return ""
        except Exception:
            pass

        text = str(text).lower()
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def contains_any(self, text, keywords):

        return any(
            keyword in text
            for keyword in keywords
        )

    def contains_regex(self, text, patterns):

        return any(
            re.search(
                pattern,
                text,
                re.IGNORECASE
            )
            for pattern in patterns
        )

    def get_conversation_type(self, message):

        return self.clean_text(
            message.get(
                "conversation_type",
                ""
            )
        )

    def get_forwarded_count(self, message):

        forwarded_count = message.get(
            "forwarded_count",
            0
        )

        try:
            if pd.isna(forwarded_count):
                return 0

            return int(forwarded_count)

        except (
            ValueError,
            TypeError
        ):
            return 0

    # ---------------------------------------------------------
    # Scam helper
    # ---------------------------------------------------------

    def is_scam_request(self, text):

        safety_words = [
            "never ask",
            "never share",
            "do not share",
            "don't share",
            "safety advisory",
            "security awareness",
            "stay safe",
            "beware of scammers",
            "never ask for otp",
            "never ask for password",
            "we will never ask",
            "brand says they never ask",
        ]

        if self.contains_any(
            text,
            safety_words
        ):
            return False

        # Clear credential / OTP theft requests.
        scam_request_patterns = [
            r"\b(?:share|send|provide|enter|give|reply with|confirm)\b.*\b(?:otp|one time password|password|login code|verification code|security code|code|pin|cvv)\b",

            r"\breply with\b.*\b\d+\s*-?\s*digit\b.*\b(?:code|otp|login code|verification code)\b",

            r"\b(?:otp|password|login code|verification code|security code)\b.*\b(?:reply|share|send|provide|enter|give|confirm)\b",

            r"\bverify now\b.*\b(?:account|login|profile)\b",

            r"\b(?:verify|confirm)\b.*\b(?:account|profile|login)\b.*\b(?:otp|password|code)\b",

            r"\baccount[- ]login\.[a-z]{2,}\b",

            r"\bprofile may be temporarily blocked\b",

            r"\b(?:account|profile|workspace access)\b.*\b(?:blocked|expire|expired|expiring)\b.*\b(?:otp|password|code|login code)\b",

            r"\bscan\b.*\bqr\b.*\bpay\b",

            r"\bpay\b.*\bfee\b.*\brelease\b",
        ]

        if self.contains_regex(
            text,
            scam_request_patterns
        ):
            return True

        # Suspicious credential term combined with
        # account-blocking / forced-action language.
        credential_terms = [
            "otp",
            "one time password",
            "password",
            "login code",
            "verification code",
            "security code",
            "6 digit code",
            "6-digit code",
            "cvv",
            "card pin",
            "upi pin",
        ]

        threat_terms = [
            "verify now",
            "confirm now",
            "blocked",
            "temporarily blocked",
            "account active",
            "keep access active",
            "keep payments active",
            "may have leaked",
            "security alert",
            "access will expire",
            "access expire today",
        ]

        has_credential = self.contains_any(
            text,
            credential_terms
        )

        has_threat = self.contains_any(
            text,
            threat_terms
        )

        if has_credential and has_threat:
            return True

        return False

    # ---------------------------------------------------------
    # Work urgency helper
    # ---------------------------------------------------------

    def is_work_urgent(self, text):

        work_urgency_patterns = [
            r"\bprod review\b.*\b(?:pulled|moved|shifted)\b",
            r"\b(?:need|needs)\b.*\b(?:close|finish|complete)\b.*\b(?:eod|end of day)\b",
            r"\bbefore eod\b",
            r"\bend of day\b",
            r"\bneed to close\b",
            r"\blast[- ]minute\b",
            r"\bcan you join\b.*\b(?:need|before|close)\b",
            r"\bescalation starts\b.*\b\d+\s*minutes?\b",
            r"\bretry count crossed\b.*\bthreshold\b",
        ]

        return self.contains_regex(
            text,
            work_urgency_patterns
        )

    # ---------------------------------------------------------
    # Message type detection
    # ---------------------------------------------------------

    def detect_message_type(self, message, text):

        conversation_type = (
            self.get_conversation_type(message)
        )

        forwarded_count = (
            self.get_forwarded_count(message)
        )

        # -----------------------------------------------------
        # 1. SCAM
        # -----------------------------------------------------

        if self.contains_any(
            text,
            self.injection_keywords
        ):
            return "scam"

        if self.is_scam_request(text):
            return "scam"

        safety_words = [
            "never ask",
            "never share",
            "do not share",
            "don't share",
            "safety advisory",
            "security awareness",
            "stay safe",
            "beware of scammers",
            "never ask for otp",
            "never ask for password",
            "we will never ask",
        ]

        is_safety_advisory = (
            self.contains_any(
                text,
                safety_words
            )
        )

        scam_matches = sum(
            1
            for keyword in self.scam_keywords
            if keyword in text
        )

        if (
            scam_matches >= 2
            and not is_safety_advisory
        ):
            return "scam"

        # -----------------------------------------------------
        # 2. SPAM
        # -----------------------------------------------------

        spam_keywords = [
            "senior admission counselor",
            "call back at another time",
            "not able to hear you",
            "are we still online",
            "busy at the moment",
            "congratulations you have been selected",
            "limited seats call now",
            "you have won",
        ]

        spam_matches = sum(
            1
            for keyword in spam_keywords
            if keyword in text
        )

        spam_patterns = [
            r"\bclick\s+(the\s+)?link\b.*\bwin\b",
            r"\byou have won\b",
            r"\bguaranteed income\b",
            r"\bwork from home\b.*\bearn\b",
        ]

        if (
            spam_matches >= 2
            or (
                spam_matches >= 1
                and self.contains_regex(
                    text,
                    spam_patterns
                )
            )
        ):
            return "spam"

        # -----------------------------------------------------
        # 3. SAFETY ADVISORY
        # -----------------------------------------------------

        if is_safety_advisory:
            return "business_update"

        # -----------------------------------------------------
        # 4. URGENT WORK
        #
        # Must come before promotion because words such as
        # "client", "screenshots" or business context must not
        # override a direct EOD deadline.
        # -----------------------------------------------------

        if self.is_work_urgent(text):
            return "urgent"

        # -----------------------------------------------------
        # 5. PROMOTION
        # -----------------------------------------------------

        selling_keywords = [
            "selling",
            "for sale",
            "dm if interested",
            "price",
            "rs ",
            "₹",
            "bought last year",
            "not using it anymore",
            "photos for the",
            "pickup near",
            "pickup is near",
            "medium size",
            "brand new",
            "available for",
            "message me if interested",
        ]

        promotion_patterns = [
            r"\b\d+\s*%\s*off\b",
            r"\bsave\s+₹?\s*\d+",
            r"\bonly\s+₹?\s*\d+",
            r"\bprice\s*[:\-]?\s*₹?\s*\d+",
            r"\brs\.?\s*\d+",
            r"\b₹\s*\d+",
            r"\bflat\s+\d+\s*%\b",
        ]

        if (
            self.contains_any(
                text,
                self.promotion_keywords
            )
            or self.contains_any(
                text,
                selling_keywords
            )
            or self.contains_regex(
                text,
                promotion_patterns
            )
        ):
            return "promotion"

        # -----------------------------------------------------
        # 6. GREETING
        # -----------------------------------------------------

        greeting_keywords = [
            "good morning",
            "good night",
            "good afternoon",
            "good evening",
            "hope today is peaceful",
            "good vibes",
            "have a great day",
            "have a nice day",
            "happy birthday",
            "happy anniversary",
            "wish you a wonderful day",
        ]

        if self.contains_any(
            text,
            greeting_keywords
        ):
            return "greeting"

        # -----------------------------------------------------
        # 7. FORWARD / CHAIN
        # -----------------------------------------------------

        if (
            forwarded_count >= 3
            or self.contains_any(
                text,
                self.forward_keywords
            )
        ):
            return "forward"

        # -----------------------------------------------------
        # 8. EVENT
        # -----------------------------------------------------

        event_keywords = [
            "form is open",
            "cultural night",
            "bus is leaving",
            "route b parents",
            "event registration",
            "consent form",
            "field trip",
            "school circular",
            "departure time",
            "return time",
            "planned field trip",
            "trip destination",
            "appointment",
            "prescription",
            "claim",
            "pickup details",
            "meeting at",
            "meeting is",
            "class starts",
            "registration closes",
            "rsvp",
            "venue",
            "schedule",
            "pickup is",
            "drop off",
            "reporting time",
            "parents",
        ]

        event_patterns = [
            r"\bbus is leaving\b",
            r"\bkeep kids\b.*\bby\b",
            r"\bclass\b.*\bstarts?\b",
            r"\bmeeting\b.*\bat\b",
            r"\bappointment\b.*\bat\b",
            r"\bfield trip\b",
            r"\bconsent form\b",
            r"\bregistration\b.*\bopen\b",
        ]

        if (
            self.contains_any(
                text,
                event_keywords
            )
            or self.contains_regex(
                text,
                event_patterns
            )
        ):
            return "event"

        # -----------------------------------------------------
        # 9. PAYMENT
        # -----------------------------------------------------

        payment_keywords = [
            "payment received",
            "payment successful",
            "payment failed",
            "transaction successful",
            "transaction failed",
            "debited",
            "credited",
            "refund processed",
            "refund initiated",
            "invoice",
            "amount due",
            "payment due",
            "bill due",
            "upi transaction",
            "card charged",
            "charged to your card",
            "failed-payment",
            "failed payment",
        ]

        payment_patterns = [
            r"\b₹\s*\d+.*\bdebited\b",
            r"\b₹\s*\d+.*\bcredited\b",
            r"\bpayment\b.*\bfailed\b",
            r"\btransaction\b.*\bfailed\b",
            r"\bamount\b.*\bdue\b",
        ]

        if (
            self.contains_any(
                text,
                payment_keywords
            )
            or self.contains_regex(
                text,
                payment_patterns
            )
        ):
            return "payment"

        # -----------------------------------------------------
        # 10. EXPLICITLY NON-URGENT PERSONAL
        # -----------------------------------------------------

        if self.contains_any(
            text,
            self.negative_urgency_keywords
        ):
            return "personal"

        # -----------------------------------------------------
        # 11. URGENT
        # -----------------------------------------------------

        urgent_patterns = [
            r"\b\d+\s*mins?\s*(early|left|before)\b",
            r"\b\d+\s*minutes?\s*(early|left|before)\b",
            r"\blast[- ]minute\b",
            r"\bcall now\b",
            r"\bneed quick help\b",
            r"\bneed to close\b",
            r"\bcannot wait\b",
            r"\bstarts in\b",
            r"\bleaving in\b",
            r"\bin\s+\d+\s*minutes?\b",
            r"\bneed immediate help\b",
            r"\bfill drinking water now\b",
            r"\bmissed morning supply\b",
            r"\bbefore eod\b",
            r"\bend of day\b",
            r"\bjoin with\b",
            r"\bpulled to \d+\b",
            r"\bby \d{1,2}(:\d{2})?\b",
            r"\bbefore \d{1,2}(:\d{2})?\b",
        ]

        if self.contains_any(
            text,
            self.high_urgency_keywords
        ):
            return "urgent"

        if self.contains_regex(
            text,
            urgent_patterns
        ):
            return "urgent"

        # -----------------------------------------------------
        # 12. BUSINESS UPDATE
        # -----------------------------------------------------

        business_keywords = [
            "dear customer",
            "your order",
            "order ending",
            "has been packed",
            "local hub",
            "delivery details",
            "delivery-code",
            "delivery code",
            "thank you for choosing",
            "customer service",
            "service update",
            "account update",
            "order update",
            "shipment",
            "out for delivery",
            "expected to reach",
            "delivery scheduled",
            "tap below to view details",
        ]

        if (
            conversation_type == "business"
            or self.contains_any(
                text,
                business_keywords
            )
        ):
            return "business_update"

        # -----------------------------------------------------
        # 13. UNKNOWN
        # -----------------------------------------------------

        unknown_keywords = [
            "found your number",
            "volunteer sheet",
            "still coordinating",
            "who is this",
            "not sure if this is",
        ]

        if (
            not text
            or self.contains_any(
                text,
                unknown_keywords
            )
        ):
            return "unknown"

        # -----------------------------------------------------
        # 14. DEFAULT
        # -----------------------------------------------------

        return "personal"

    # ---------------------------------------------------------
    # Risk scoring
    # ---------------------------------------------------------

    def calculate_risk_score(
        self,
        message,
        text,
        context
    ):

        if self.contains_any(
            text,
            self.injection_keywords
        ):
            return 1.0

        if self.is_scam_request(text):
            return 1.0

        risk_score = 0.0

        safety_words = [
            "never ask",
            "never share",
            "do not share",
            "don't share",
            "safety advisory",
            "security awareness",
            "beware of scammers",
            "we will never ask",
        ]

        is_safety_advisory = self.contains_any(
            text,
            safety_words
        )

        scam_matches = sum(
            1
            for keyword in self.scam_keywords
            if keyword in text
        )

        if (
            scam_matches > 0
            and not is_safety_advisory
        ):
            risk_score += min(
                0.80,
                scam_matches * 0.25
            )

        conversation_type = (
            self.get_conversation_type(message)
        )

        if conversation_type == "business":

            business_context = context.get(
                "business_context",
                {}
            )

            businesses = business_context.get(
                "business",
                []
            )

            if businesses:

                business = businesses[0]

                verified = business.get(
                    "verified",
                    0
                )

                official_domain = self.clean_text(
                    business.get(
                        "official_domain",
                        ""
                    )
                )

                sender_domain = self.clean_text(
                    business.get(
                        "domain_used_by_sender",
                        ""
                    )
                )

                if not verified:
                    risk_score += 0.20

                if (
                    official_domain
                    and sender_domain
                    and official_domain != sender_domain
                ):
                    risk_score += 0.30

        history = context.get(
            "history",
            {}
        )

        related_events = history.get(
            "related_events",
            []
        )

        if related_events:

            reports = sum(
                event.get(
                    "message_reported",
                    0
                ) or 0
                for event in related_events
            )

            if reports > 0:
                risk_score += min(
                    0.25,
                    reports * 0.10
                )

        return round(
            min(
                risk_score,
                1.0
            ),
            4
        )

    # ---------------------------------------------------------
    # Urgency scoring
    # ---------------------------------------------------------

    def calculate_urgency_score(self, text):

        if self.contains_any(
            text,
            self.negative_urgency_keywords
        ):
            return 0.0

        score = 0.0

        high_matches = sum(
            1
            for keyword in self.high_urgency_keywords
            if keyword in text
        )

        medium_matches = sum(
            1
            for keyword in self.medium_urgency_keywords
            if keyword in text
        )

        if high_matches > 0:
            score += min(
                0.80,
                high_matches * 0.30
            )

        if medium_matches > 0:
            score += min(
                0.50,
                medium_matches * 0.15
            )

        if self.is_work_urgent(text):
            score += 0.35

        urgent_patterns = [
            r"\bcall now\b",
            r"\bneed quick help\b",
            r"\blast[- ]minute\b",
            r"\bneed to close\b",
            r"\bcannot wait\b",
            r"\b\d+\s*mins?\s*early\b",
            r"\b\d+\s*minutes?\s*early\b",
            r"\bin\s+\d+\s*minutes?\b",
            r"\bjoin with\b",
            r"\bfill drinking water now\b",
            r"\bmissed morning supply\b",
            r"\bbefore eod\b",
            r"\bend of day\b",
        ]

        if self.contains_regex(
            text,
            urgent_patterns
        ):
            score += 0.35

        deadline_patterns = [
            r"\b\d+\s*minutes?\b",
            r"\b\d+\s*mins?\b",
            r"\b\d+\s*hours?\b",
            r"\bby\s+\d{1,2}(:\d{2})?\s*(am|pm)?\b",
            r"\bbefore\s+\d{1,2}(:\d{2})?\s*(am|pm)?\b",
        ]

        if self.contains_regex(
            text,
            deadline_patterns
        ):
            score += 0.15

        return round(
            min(
                score,
                1.0
            ),
            4
        )

    # ---------------------------------------------------------
    # Source trust scoring
    # ---------------------------------------------------------

    def calculate_trust_score(
        self,
        message,
        context
    ):

        score = 0.50

        conversation_type = (
            self.get_conversation_type(message)
        )

        if conversation_type == "personal":
            score += 0.15

        if conversation_type == "group":

            membership = (
                context.get(
                    "group_context",
                    {}
                )
                .get(
                    "membership",
                    []
                )
            )

            if membership:
                score += 0.15

        if conversation_type == "business":

            business_context = context.get(
                "business_context",
                {}
            )

            businesses = business_context.get(
                "business",
                []
            )

            relationships = business_context.get(
                "relationship",
                []
            )

            if businesses:

                business = businesses[0]

                if business.get(
                    "verified",
                    0
                ):
                    score += 0.25
                else:
                    score -= 0.15

            if relationships:

                relationship = relationships[0]

                activity_count = relationship.get(
                    "activity_count_180d",
                    0
                )

                try:
                    activity_count = float(
                        activity_count
                    )
                except (
                    ValueError,
                    TypeError
                ):
                    activity_count = 0

                if activity_count >= 3:
                    score += 0.15
                elif activity_count > 0:
                    score += 0.08

        return round(
            max(
                0.0,
                min(
                    score,
                    1.0
                )
            ),
            4
        )

    # ---------------------------------------------------------
    # Historical engagement scoring
    # ---------------------------------------------------------

    def calculate_engagement_score(self, context):

        history = context.get(
            "history",
            {}
        )

        relevant_history = history.get(
            "relevant_history",
            []
        )

        related_events = history.get(
            "related_events",
            []
        )

        if not relevant_history:
            return 0.50

        events_by_id = {
            event.get("message_id"): event
            for event in related_events
        }

        scores = []

        for historical_message in relevant_history:

            message_id = historical_message.get(
                "message_id"
            )

            similarity = historical_message.get(
                "similarity_score",
                0.0
            )

            try:
                similarity = float(similarity)
            except (
                ValueError,
                TypeError
            ):
                similarity = 0.0

            event = events_by_id.get(
                message_id,
                {}
            )

            score = 0.40

            if event.get(
                "message_opened",
                0
            ):
                score += 0.20

            if event.get(
                "message_replied",
                0
            ):
                score += 0.20

            reaction_time = event.get(
                "reaction_time_minutes",
                None
            )

            if (
                reaction_time is not None
                and pd.notna(reaction_time)
            ):
                try:

                    reaction_time = float(
                        reaction_time
                    )

                    if reaction_time <= 5:
                        score += 0.15

                    elif reaction_time <= 30:
                        score += 0.10

                except (
                    ValueError,
                    TypeError
                ):
                    pass

            weighted_score = (
                score * similarity
                + 0.50 * (1 - similarity)
            )

            scores.append(
                weighted_score
            )

        if not scores:
            return 0.50

        return round(
            min(
                max(
                    sum(scores) / len(scores),
                    0.0
                ),
                1.0
            ),
            4
        )

    # ---------------------------------------------------------
    # Negative history scoring
    # ---------------------------------------------------------

    def calculate_negative_history_score(
        self,
        context
    ):

        history = context.get(
            "history",
            {}
        )

        events = history.get(
            "related_events",
            []
        )

        if not events:
            return 0.0

        total_penalty = 0.0

        for event in events:

            if event.get(
                "notification_dismissed",
                0
            ):
                total_penalty += 0.20

            if event.get(
                "muted_after_message",
                0
            ):
                total_penalty += 0.40

            if event.get(
                "message_reported",
                0
            ):
                total_penalty += 0.30

        average_penalty = (
            total_penalty / len(events)
        )

        return round(
            min(
                average_penalty,
                1.0
            ),
            4
        )

    # ---------------------------------------------------------
    # Notification overload
    # ---------------------------------------------------------

    def calculate_notification_overload(
        self,
        context
    ):

        summaries = context.get(
            "notification_summary",
            []
        )

        if not summaries:
            return 0.0

        recent_summaries = summaries[-7:]

        sent_values = []

        for item in recent_summaries:

            value = item.get(
                "notifications_sent",
                0
            )

            try:
                sent_values.append(
                    float(value)
                )
            except (
                ValueError,
                TypeError
            ):
                pass

        if not sent_values:
            return 0.0

        average_sent = (
            sum(sent_values)
            / len(sent_values)
        )

        if average_sent >= 15:
            return 0.30

        if average_sent >= 10:
            return 0.20

        if average_sent >= 7:
            return 0.10

        return 0.0

    # ---------------------------------------------------------
    # Evidence selection
    # ---------------------------------------------------------

    def select_evidence(
        self,
        context,
        limit=3
    ):

        history = context.get(
            "history",
            {}
        )

        relevant_history = history.get(
            "relevant_history",
            []
        )

        if not relevant_history:
            return "none"

        evidence_ids = []

        for item in relevant_history[:limit]:

            similarity = item.get(
                "similarity_score",
                0.0
            )

            message_id = item.get(
                "message_id"
            )

            try:
                similarity = float(similarity)
            except (
                ValueError,
                TypeError
            ):
                similarity = 0.0

            if (
                message_id
                and similarity >= 0.10
            ):
                evidence_ids.append(
                    str(message_id)
                )

        if not evidence_ids:
            return "none"

        return ";".join(
            evidence_ids
        )

    # ---------------------------------------------------------
    # Final routing decision
    # ---------------------------------------------------------

    def decide(
        self,
        message,
        context
    ):

        raw_text = message.get(
            "message_text",
            ""
        )

        text = self.clean_text(
            raw_text
        )

        message_type = self.detect_message_type(
            message,
            text
        )

        risk_score = self.calculate_risk_score(
            message,
            text,
            context
        )

        urgency_score = self.calculate_urgency_score(
            text
        )

        trust_score = self.calculate_trust_score(
            message,
            context
        )

        engagement_score = (
            self.calculate_engagement_score(
                context
            )
        )

        negative_history_score = (
            self.calculate_negative_history_score(
                context
            )
        )

        notification_overload = (
            self.calculate_notification_overload(
                context
            )
        )

        # -----------------------------------------------------
        # FINAL ROUTING RULES
        # -----------------------------------------------------

        if (
            message_type == "scam"
            or risk_score >= 0.65
        ):
            action = "mute"

        elif message_type == "spam":
            action = "mute"

        elif message_type == "promotion":

            if negative_history_score >= 0.30:
                action = "mute"
            else:
                action = "digest"

        elif message_type == "forward":

            if negative_history_score >= 0.10:
                action = "mute"
            else:
                action = "digest"

        elif message_type == "greeting":

            if negative_history_score >= 0.20:
                action = "mute"
            else:
                action = "digest"

        elif (
            message_type == "event"
            and negative_history_score < 0.40
            and (
                urgency_score >= 0.15
                or engagement_score >= 0.70
                or self.contains_any(
                    text,
                    [
                        "consent form",
                        "school circular",
                        "field trip",
                        "departure time",
                        "return time",
                        "appointment",
                        "prescription",
                        "claim",
                        "pickup details",
                        "bus is leaving",
                        "route b parents",
                    ]
                )
            )
        ):
            action = "notify"

        elif (
            message_type == "urgent"
            and trust_score >= 0.55
            and negative_history_score < 0.40
        ):
            action = "notify"

        elif (
            message_type == "payment"
            and trust_score >= 0.55
            and negative_history_score < 0.40
            and (
                urgency_score >= 0.15
                or self.contains_any(
                    text,
                    [
                        "payment failed",
                        "transaction failed",
                        "amount due",
                        "payment due",
                    ]
                )
            )
        ):
            action = "notify"

        elif (
            message_type == "business_update"
            and (
                urgency_score >= 0.15
                or self.contains_any(
                    text,
                    [
                        "delivery today",
                        "local hub today",
                        "expected to reach",
                    ]
                )
            )
            and trust_score >= 0.55
            and negative_history_score < 0.40
        ):
            action = "notify"

        elif (
            message_type == "personal"
            and trust_score >= 0.60
            and negative_history_score < 0.30
            and not self.contains_any(
                text,
                self.negative_urgency_keywords
            )
            and self.contains_any(
                text,
                [
                    "can you call",
                    "please call",
                    "call me",
                    "before i confirm",
                    "confirm cab count",
                    "can you come",
                    "can you join",
                    "need your help",
                ]
            )
        ):
            action = "notify"

        elif (
            engagement_score >= 0.70
            and trust_score >= 0.60
            and negative_history_score < 0.30
            and notification_overload < 0.25
            and message_type not in [
                "personal",
                "greeting",
                "promotion",
                "forward",
            ]
        ):
            action = "notify"

        else:
            action = "digest"

        confidence = (
            0.45
            + abs(
                risk_score - 0.50
            ) * 0.20
            + urgency_score * 0.10
            + abs(
                engagement_score - 0.50
            ) * 0.20
            + trust_score * 0.10
        )

        confidence = max(
            0.65,
            min(
                confidence,
                0.95
            )
        )

        evidence_message_ids = (
            self.select_evidence(
                context
            )
        )

        return {
            "message_id": message[
                "message_id"
            ],
            "action": action,
            "message_type": message_type,
            "confidence": round(
                confidence,
                4
            ),
            "evidence_message_ids": evidence_message_ids,
            "debug_scores": {
                "risk_score": risk_score,
                "urgency_score": urgency_score,
                "trust_score": trust_score,
                "engagement_score": engagement_score,
                "negative_history_score": negative_history_score,
                "notification_overload": notification_overload,
            },
        }
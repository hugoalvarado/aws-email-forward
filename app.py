from aws_cdk import (
    aws_s3 as s3,
    aws_sns as sns,
    aws_ses as ses,
    aws_ses_actions as actions,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    App, Duration, Stack
)

verified_recepient_email = "hugo@hugoalvarado.net"


class EmailForwardStack(Stack):
    def __init__(self, app: App, id: str) -> None:
        super().__init__(app, id)

        with open("lambda-handler.py", encoding="utf8") as fp:
            handler_code = fp.read()

        lambda_fn = lambda_.Function(
            self, "Singleton",
            code=lambda_.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_7,
        )

        # s3 bucket
        s3_bucket = s3.Bucket(self, "EmailBucket")
        s3_bucket.grant_read(lambda_fn)

        # iam policy
        # iam role

        # ses
        topic = sns.Topic(self, "TopicSnsForEmail")

        ses.ReceiptRuleSet(self, "RuleSetEmail",
                           rules=[ses.ReceiptRuleOptions(
                               recipients=[verified_recepient_email],
                               actions=[
                                   actions.S3(
                                       bucket=s3_bucket,
                                       object_key_prefix="emails/",
                                       topic=topic
                                   ),
                                   actions.Lambda(
                                       function=lambda_fn,
                                       topic=topic

                                   )
                               ]
                           )
                           ]
                           )


app = App()
EmailForwardStack(app, "EmailForwardStack")
app.synth()

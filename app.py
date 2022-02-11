from aws_cdk import (
    aws_s3 as s3,
    aws_sns as sns,
    aws_ses as ses,
    aws_iam as iam,
    aws_ses_actions as actions,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    App, Duration, Stack
)

# TODO: make this configurable - hardcode..bad
verified_recipient_email = "hugo@hugoalvarado.net"
subscription_email = "hugo102@gmail.com"
s3_bucket_prefix = "emails"


class EmailForwardStack(Stack):
    def __init__(self, app: App, id: str) -> None:
        super().__init__(app, id)

        # TODO: create verified identities (the emails) in SES

        # s3 bucket
        s3_bucket = s3.Bucket(self, "EmailBucket")

        with open("lambda-handler.py", encoding="utf8") as fp:
            handler_code = fp.read()

        lambda_fn = lambda_.Function(
            self, "EmailHandler",
            code=lambda_.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_7,
            environment={
                "Region": self.region,
                "MailSender": verified_recipient_email,
                "MailRecipient": subscription_email,
                "MailS3Bucket": s3_bucket.bucket_name,
                "MailS3Prefix": s3_bucket_prefix
            },
        )

        # ses
        topic = sns.Topic(self, "TopicSnsForEmail")
        subscription = sns.Subscription(self, "emailForwardSubscription",
                                        topic=topic,
                                        endpoint=subscription_email,
                                        protocol=sns.SubscriptionProtocol.EMAIL
                                        )

        # sns
        ses.ReceiptRuleSet(self, "RuleSetEmail",
                           rules=[ses.ReceiptRuleOptions(
                               recipients=[verified_recipient_email],
                               actions=[
                                   actions.S3(
                                       bucket=s3_bucket,
                                       object_key_prefix=s3_bucket_prefix + "/",
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

        # permissions
        s3_bucket.grant_read(lambda_fn)

        # iam policy with ses:SendRawEmail
        ses_arn = 'arn:aws:ses:{}:{}:identity/{}'.format(
            self.region,
            self.account,
            verified_recipient_email)
        lambda_fn.role.add_to_policy(
            iam.PolicyStatement(
                actions=['ses:SendEmail', 'SES:SendRawEmail'],
                resources=[ses_arn],
                effect=iam.Effect.ALLOW
            ))


app = App()
EmailForwardStack(app, "EmailForwardStack")
app.synth()

import csv
import io

from app.modules.analysis.models import Analysis


def build_analysis_csv(analysis: Analysis) -> str:
    """Build a CSV file from an analysis.
    Args:
        analysis: The analysis to build the CSV file from.
    Returns:
        A string with the CSV file.
    Example:
        section,key,value
        summary,analysis_id,...
        summary,monthly_recurring_total,...
        summary,estimated_savings,...
        summary,created_at,...

        section,merchant,amount,cadence,category
        subscription,NETFLIX,15.49,monthly,streaming
        ...

        section,title,detail,estimated_saving,kind
        recommendation,...,...,...,cancel_subscription

    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Summary
    writer.writerow(["section", "key", "value"])
    writer.writerow(["summary", "analysis_id", analysis.id])
    writer.writerow(["summary", "monthly_recurring_total", analysis.monthly_recurring_total])
    writer.writerow(["summary", "estimated_savings", analysis.estimated_savings])
    writer.writerow(["summary", "created_at", analysis.created_at])

    # Subscriptions
    writer.writerow(["subscription", "merchant", "amount", "cadence", "category"])
    for subscription in analysis.detected_subscriptions:
        writer.writerow(
            [
                "subscription", 
                subscription.merchant, 
                subscription.amount, 
                subscription.cadence, 
                subscription.category
            ]
        )
    
    # Recommendations
    writer.writerow(["recommendation", "title", "detail", "estimated_saving", "kind"])
    for recommendation in analysis.recommendations:
        writer.writerow(
            [
                "recommendation", 
                recommendation.title, 
                recommendation.detail, 
                recommendation.estimated_saving, 
                recommendation.kind
            ]
        )


    return buffer.getvalue()
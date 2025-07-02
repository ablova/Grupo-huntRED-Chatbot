import collections

gpt_usage_log = []  # En producción, usar base de datos o sistema de logging

def log_gpt_call(provider, channel, business_unit, client):
    gpt_usage_log.append({
        'provider': provider,
        'channel': channel,
        'business_unit': business_unit,
        'client': client
    })

def get_gpt_usage_stats():
    stats = {
        'total': len(gpt_usage_log),
        'by_provider': collections.Counter([x['provider'] for x in gpt_usage_log]),
        'by_channel': collections.Counter([x['channel'] for x in gpt_usage_log]),
        'by_business_unit': collections.Counter([x['business_unit'] for x in gpt_usage_log]),
        'by_client': collections.Counter([x['client'] for x in gpt_usage_log]),
    }
    return stats 
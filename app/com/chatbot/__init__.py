from ..lazy_imports import lazy_imports, register_module, get_module

# Establecer el paquete actual
register_module('chatbot', '.', package='app.com.chatbot')

# Registrar módulos de chatbot para lazy loading
register_module('channel_config', '.channel_config', package='app.com.chatbot')
register_module('chat_state_manager', '.chat_state_manager', package='app.com.chatbot')
register_module('chatbot', '.chatbot', package='app.com.chatbot')
register_module('context_manager', '.context_manager', package='app.com.chatbot')
register_module('conversational_flow', '.conversational_flow', package='app.com.chatbot')
register_module('extractors', '.extractors', package='app.com.chatbot')
register_module('generate_embeddings', '.generate_embeddings', package='app.com.chatbot')
register_module('gpt', '.gpt', package='app.com.chatbot')
register_module('integrations', '.integrations', package='app.com.chatbot')
register_module('intents_handler', '.intents_handler', package='app.com.chatbot')
register_module('intents_optimizer', '.intents_optimizer', package='app.com.chatbot')
register_module('message_retry', '.message_retry', package='app.com.chatbot')
register_module('metrics', '.metrics', package='app.com.chatbot')
register_module('migration_check', '.migration_check', package='app.com.chatbot')
register_module('nlp', '.nlp', package='app.com.chatbot')
register_module('optimization_config', '.optimization_config', package='app.com.chatbot')
register_module('start_metrics', '.start_metrics', package='app.com.chatbot')
register_module('state_manager', '.state_manager', package='app.com.chatbot')
register_module('utils', '.utils', package='app.com.chatbot')
register_module('whatsapp_handler', '.whatsapp_handler', package='app.com.chatbot')
register_module('workflow', '.workflow', package='app.com.chatbot')
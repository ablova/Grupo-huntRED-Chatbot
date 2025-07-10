module.exports = {
  apps: [
    {
      name: 'huntred-frontend',
      script: 'npm',
      args: 'run dev',
      cwd: '/home/pablo/ai_huntred/app/templates/front',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      error_file: '/home/pablo/ai_huntred/logs/frontend-error.log',
      out_file: '/home/pablo/ai_huntred/logs/frontend-out.log',
      log_file: '/home/pablo/ai_huntred/logs/frontend-combined.log',
      time: true
    }
  ]
}; 
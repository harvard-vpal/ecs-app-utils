[
    {
    "name": "worker",
    "image": "${image}",
    "essential": true,
    "memory": 256,
    "command": [
      "celery",
      "-A",
      "config",
      "worker",
      "-l",
      "info"
    ],
    "environment": [
      {"name": "DJANGO_SETTINGS_MODULE", "value": "config.settings.eb.dev"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${log_group_name}",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }
]

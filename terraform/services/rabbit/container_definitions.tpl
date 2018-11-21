[
  {
    "name": "rabbit",
    "image": "rabbitmq",
    "essential": true,
    "memory": 256,
    "environment": [
      {"name": "RABBITMQ_DEFAULT_PASS", "value": "bridge_celery_password"},
      {"name": "RABBITMQ_DEFAULT_USER", "value": "bridge_celery_user"}
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

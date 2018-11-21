[
  {
    "name": "web",
    "image": "${web_image}",
    "essential": true,
    "memory": 256,
    "portMappings": [
      {
        "containerPort": 8000
      }
    ],
    "command": [
      "/usr/local/bin/gunicorn",
      "config.wsgi:application",
      "-w=2",
      "-b=:8000",
      "--log-level=debug",
      "--log-file=-",
      "--access-logfile=-"
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
  },
  {
    "name": "nginx",
    "image": "${nginx_image}",
    "essential": false,
    "memory": 256,
    "portMappings": [
      {
        "containerPort": 80
      }
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

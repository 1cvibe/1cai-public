# Ansible Bootstrap Playbook

> Назначение: подготовка Linux-хоста (Ubuntu/Debian) к запуску 1C AI Stack (Docker, Kubernetes toolchain, Helm, Terraform, Ansible deps).

## Запуск
```bash
cd infrastructure/ansible
ansible-playbook -i hosts.ini site.yml --ask-become-pass
```

## hosts.ini (пример)
```
[dev]
node1 ansible_host=192.168.1.20 ansible_user=ubuntu
```

## Что делает playbook
- Обновляет apt, устанавливает Docker, kubectl, Helm, Terraform.
- Настраивает пользователя в группе `docker`.
- Устанавливает Python-зависимости (pip, virtualenv, ansible deps).
- Создаёт директорию `/opt/1cai` и копирует makefile/скрипты по желанию.

## TODO
- Роли для AWS/Azure (установка CLI, настройка профилей).
- Интеграция с Ansible Galaxy (docker, kubectl роли).
- CI job (`ansible-lint`).

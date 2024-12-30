#!/bin/bash

# Configurações de conexão com o MySQL
MYSQL_USER="your username"
MYSQL_PASSWORD="your root password"
MYSQL_HOST="localhost"

# Diretório contendo os arquivos .sql
DUMP_DIR="$(pwd)"

# Loop por cada arquivo .sql no diretório
for SQL_FILE in "$DUMP_DIR"/*.sql; do
    # Extrai o nome do banco de dados do nome do arquivo
    DB_NAME=$(basename "$SQL_FILE" .sql)

    echo "Importando $SQL_FILE para a database $DB_NAME..."

    # Cria a database, caso não exista
    mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -h"$MYSQL_HOST" -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`;"

    # Importa o arquivo SQL para a database
    mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -h"$MYSQL_HOST" "$DB_NAME" < "$SQL_FILE"

    # Criação de usuários e privilégios (descomente isto para criar apenas um user e dar privilegios para todas as dbs)
    # mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -h"$MYSQL_HOST" -e "
    # CREATE USER 'USER'@'%' IDENTIFIED BY 'PASSWORD';
    # GRANT ALL PRIVILEGES ON "$DB_NAME".* TO 'USER'@'%' WITH GRANT OPTION;
    # FLUSH PRIVILEGES;
    # "

    echo "Importação de $SQL_FILE e criação de user com privilegios concluída para $DB_NAME."
done

echo "Todas as databases foram importadas com sucesso."
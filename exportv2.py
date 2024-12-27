import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import subprocess
import os

kubeconfig_file_path = "kubeconfig_path.txt"

def executar_comando(comando):
    """Executa um comando no terminal e retorna a saída."""
    if "KUBECONFIG" in os.environ:
        comando = f"KUBECONFIG={os.environ['KUBECONFIG']} {comando}"
    processo = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    saida, erro = processo.communicate()
    if erro:
        return f"Erro: {erro}"
    return saida

def copiar_arquivo():
    """Copia um arquivo SQL existente do pod."""
    namespace = namespace_entry.get()
    pod_name = pod_listbox.get(tk.ANCHOR)
    if not namespace or not pod_name:
        saida_text.insert(tk.END, "Erro: Selecione um namespace e um pod.\n")
        return

    # Listar os arquivos .sql no diretório /tmp do pod
    comando_ls = f"kubectl exec -it {pod_name} -n {namespace} -- ls /tmp/"
    saida_ls = executar_comando(comando_ls)
    if "Erro" in saida_ls:
        saida_text.insert(tk.END, saida_ls + "\n")
        return

    arquivos = saida_ls.splitlines()
    if not arquivos:
        saida_text.insert(tk.END, "Nenhum arquivo .sql encontrado no diretório /tmp do pod.\n")
        return

    # Exibir a lista de arquivos em uma caixa de diálogo para o usuário escolher
    file_name = simpledialog.askstring(
        "Selecione um arquivo",
        "Arquivos disponíveis:\n" + "\n".join(arquivos),
        parent=janela
    )
    if not file_name:
        return


    comando = f"kubectl cp {pod_name}:/tmp/{file_name} ./{file_name} -n {namespace}"
    saida = executar_comando(comando)
    saida_text.insert(tk.END, saida + "COPIADO COM SUCESSO! \n")

def criar_dump():
    """Cria um novo dump do banco de dados."""
    namespace = namespace_entry.get()
    pod_name = pod_listbox.get(tk.ANCHOR)
    mysql_user = usuario_entry.get()
    mysql_password = senha_entry.get()
    db_name = banco_entry.get()
    if not all([namespace, pod_name, mysql_user, mysql_password, db_name]):
        saida_text.insert(tk.END, "Erro: Preencha todos os campos.\n")
        return

    comando = f"kubectl exec -it {pod_name} -n {namespace} -- bash -c \"mysqldump -u{mysql_user} -p{mysql_password} {db_name} > /tmp/{pod_name}.sql\""
    saida = executar_comando(comando)
    if "Erro" in saida:
        saida_text.insert(tk.END, saida + "\n")
        return

    comando = f"kubectl cp {pod_name}:/tmp/{pod_name}.sql {pod_name}.sql -n {namespace}"
    saida = executar_comando(comando)
    saida_text.insert(tk.END, saida + "CRIADO COM SUCESSO! \n")

def atualizar_pods():
    """Atualiza a lista de pods."""
    namespace = namespace_entry.get()
    if not namespace:
        saida_text.insert(tk.END, "Erro: Digite um namespace.\n")
        return

    comando = f"kubectl get pods -n {namespace} -o name | grep 'mysql'"
    saida = executar_comando(comando)
    if "Erro" in saida:
        saida_text.insert(tk.END, saida + "\n")
        return

    pods = [linha.split("/")[1] for linha in saida.splitlines()]
    pod_listbox.delete(0, tk.END)
    for pod in pods:
        pod_listbox.insert(tk.END, pod)

def usar_kubeconfig(kubeconfig_file):
    """Define a variável de ambiente KUBECONFIG."""
    os.environ["KUBECONFIG"] = kubeconfig_file
    saida_text.insert(tk.END, f"Usando o arquivo kubeconfig '{kubeconfig_file}'.\n")
    with open(kubeconfig_file_path, "w") as f:
        f.write(kubeconfig_file)

def selecionar_kubeconfig():
    """Permite que o usuário selecione um arquivo kubeconfig."""
    file_types = [("Arquivos Kubeconfig", "*.kubeconfig"), ("Todos os arquivos", "*.*")]
    kubeconfig_file = filedialog.askopenfilename(
        initialdir="~/Documents",
        title="Selecione um arquivo kubeconfig",
        filetypes=file_types
    )
    if kubeconfig_file:
        usar_kubeconfig(kubeconfig_file)

def verificar_kubeconfig():
    """Verifica se o arquivo kubeconfig_path.txt existe e contém um caminho válido."""
    if os.path.exists(kubeconfig_file_path):
        with open(kubeconfig_file_path, "r") as f:
            kubeconfig_file = f.read().strip()
        if os.path.exists(kubeconfig_file):
            usar_kubeconfig(kubeconfig_file)
            return
def exportar_todos_dbs():
    """Exporta todos os bancos de dados em um único arquivo SQL."""
    namespace = namespace_entry.get()
    pod_name = pod_listbox.get(tk.ANCHOR)
    mysql_user = usuario_entry.get()
    mysql_password = senha_entry.get()
    if not all([namespace, pod_name, mysql_user, mysql_password]):
        saida_text.insert(tk.END, "Erro: Preencha o namespace, pod, usuário e senha.\n")
        return

    # Executar o mysqldump para todos os bancos de dados
    comando = f"kubectl exec -it {pod_name} -n {namespace} -- bash -c \"mysqldump -u{mysql_user} -p{mysql_password} --databases --all-databases > /tmp/all_databases.sql\""  # noqa: E501
    saida = executar_comando(comando)
    if "Erro" in saida:
        saida_text.insert(tk.END, saida + "CRIANDO DOCUMENTO .sql !\n")
        return

    # Copiar o arquivo de dump
    comando = f"kubectl cp {pod_name}:/tmp/all_databases.sql all_databases.sql -n {namespace}"  # noqa: E501
    saida = executar_comando(comando)
    saida_text.insert(tk.END, saida + "EXPORTADO COM SUCESSO! \n")

    kubeconfig_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(os.path.expanduser("~/Documents"))
        for file in files
        if file.endswith(".kubeconfig")
    ]
    if kubeconfig_files:
        resultado = messagebox.askquestion(
            "Kubeconfig",
            f"Arquivos kubeconfig encontrados em ~/Documents:\n{chr(10).join(kubeconfig_files)}\n\nDeseja usar algum?",
            type="yesno"
        )
        if resultado == "yes":
            selecionar_kubeconfig()
    else:
        messagebox.showinfo("Kubeconfig", "Nenhum arquivo kubeconfig encontrado em ~/Documents.")
def importar_arquivo_sql():
    """Importa um arquivo SQL para o banco de dados MySQL do pod."""
    namespace = namespace_entry.get()
    pod_name = pod_listbox.get(tk.ANCHOR)
    mysql_user = usuario_entry.get()
    mysql_password = senha_entry.get()
    db_name = banco_entry.get()
    
    if not all([namespace, pod_name, mysql_user, mysql_password, db_name]):
        saida_text.insert(tk.END, "Erro: Preencha todos os campos.\n")
        return

    # Seleciona o arquivo SQL para importação
    file_path = filedialog.askopenfilename(
        title="Selecione o arquivo SQL",
        filetypes=[("Arquivos SQL", "*.sql"), ("Todos os arquivos", "*.*")]
    )
    if not file_path:
        return

    # Copiar o arquivo SQL para o pod
    comando_cp = f"kubectl cp {file_path} {pod_name}:/tmp/{os.path.basename(file_path)} -n {namespace}"
    saida_cp = executar_comando(comando_cp)
    if "Erro" in saida_cp:
        saida_text.insert(tk.END, saida_cp + "\n")
        return

    # Importar o arquivo SQL para o banco de dados no pod
    comando_import = f"kubectl exec -it {pod_name} -n {namespace} -- bash -c \"mysql -u{mysql_user} -p{mysql_password} {db_name} < /tmp/{os.path.basename(file_path)}\""
    saida_import = executar_comando(comando_import)
    if "Erro" in saida_import:
        saida_text.insert(tk.END, saida_import + "\n")
        return

    saida_text.insert(tk.END, f"Arquivo {os.path.basename(file_path)} importado com sucesso para o banco de dados {db_name}.\n")

# Criar a janela principal
janela = tk.Tk()
janela.title("Gerenciador de Kubeconfig e MySQL")
janela.geometry("500x600")  # Definindo o tamanho da janela
janela.config(bg="#f4f4f4")  # Cor de fundo suave

# --- Frame para o namespace ---
namespace_frame = ttk.Frame(janela, padding="10 10 10 10")
namespace_frame.pack(fill=tk.X, padx=15, pady=5)

namespace_label = ttk.Label(namespace_frame, text="Namespace:", font=("Arial", 10, "bold"), background="#f4f4f4")
namespace_label.pack(side=tk.LEFT, padx=5)

namespace_entry = ttk.Entry(namespace_frame, font=("Arial", 10))
namespace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

atualizar_button = ttk.Button(namespace_frame, text="Listar Pods", command=atualizar_pods, style="TButton")
atualizar_button.pack(side=tk.LEFT, padx=5)

# --- Frame para a lista de pods ---
pod_frame = ttk.Frame(janela, padding="10 10 10 10", relief="solid", borderwidth=1)
pod_frame.pack(fill=tk.X, padx=15, pady=10)

pod_label = ttk.Label(pod_frame, text="Pods MySQL:", font=("Arial", 10, "bold"), background="#f4f4f4")
pod_label.pack()

pod_listbox = tk.Listbox(pod_frame, font=("Arial", 10), height=4)
pod_listbox.pack(fill=tk.X, padx=5, pady=5)

# --- Frame para as opções de arquivo ---
arquivo_frame = ttk.Frame(janela, padding="10 10 10 10")
arquivo_frame.pack(fill=tk.X, padx=15, pady=10)

copiar_button = ttk.Button(arquivo_frame, text="Download Existent SQL (POD)", command=copiar_arquivo, style="TButton")
copiar_button.pack(pady=5, fill=tk.X)

# --- Frame para as opções de dump ---
dump_frame = ttk.Frame(janela, padding="10 10 10 10")
dump_frame.pack(fill=tk.X, padx=15, pady=10)

usuario_label = ttk.Label(dump_frame, text="Usuário MySQL:", font=("Arial", 10, "bold"))
usuario_label.pack(anchor=tk.W)

usuario_entry = ttk.Entry(dump_frame, font=("Arial", 10))
usuario_entry.pack(fill=tk.X, padx=5, pady=5)

senha_label = ttk.Label(dump_frame, text="Senha MySQL:", font=("Arial", 10, "bold"))
senha_label.pack(anchor=tk.W)

senha_entry = ttk.Entry(dump_frame, font=("Arial", 10), show="*")
senha_entry.pack(fill=tk.X, padx=5, pady=5)

banco_label = ttk.Label(dump_frame, text="Banco de dados:", font=("Arial", 10, "bold"))
banco_label.pack(anchor=tk.W)

banco_entry = ttk.Entry(dump_frame, font=("Arial", 10))
banco_entry.pack(fill=tk.X, padx=5, pady=5)

criar_dump_button = ttk.Button(dump_frame, text="DUMP and Download", command=criar_dump, style="TButton")
criar_dump_button.pack(pady=5, fill=tk.X)

# Criar botão para exportar todos os bancos de dados
exportar_todos_dbs_button = ttk.Button(dump_frame, text="Export all dbs from POD", command=exportar_todos_dbs, style="TButton")
exportar_todos_dbs_button.pack(pady=5, fill=tk.X)

# Adicionar botão para importar arquivo SQL
importar_button = ttk.Button(arquivo_frame, text="Import Local SQL to POD", command=importar_arquivo_sql, style="TButton")
importar_button.pack(pady=5, fill=tk.X)

# --- Frame para a saída de texto ---
saida_frame = ttk.Frame(janela, padding="10 10 10 10")
saida_frame.pack(fill=tk.BOTH, padx=15, pady=10)

saida_text = tk.Text(saida_frame, wrap=tk.WORD, font=("Arial", 10), height=6)
saida_text.pack(fill=tk.BOTH, padx=5, pady=5)

# Estilo personalizado para os botões
style = ttk.Style()
style.configure("TButton", font=("Arial", 10), padding=6, relief="flat", background="#4CAF50", foreground="white")
style.map("TButton", background=[("active", "#45a049"), ("pressed", "#388e3c")])

# Verificar kubeconfig ao iniciar a aplicação
verificar_kubeconfig()

# Executar a aplicação
janela.mainloop()
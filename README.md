# DetectiveLab

Aplicação web-mobile para investigadores: organize livros como "casos", monte quadros de investigação com anotações e fios, importe texto de imagens via OCR, compartilhe evidências e estude os mestres da literatura de mistério.

O projeto tem duas partes que conversam por uma API REST:

- **Backend (Django + Django REST Framework)** — o site web e a API consumida pelo app.
- **App mobile (Ionic + Angular)** — consome a API por meio de serviços.

---

## Instalação (Ubuntu)

Estas instruções assumem um Ubuntu/Debian limpo. Você vai precisar de dois ambientes independentes: **Python** (backend) e **Node.js** (app mobile).

### Pré-requisitos do sistema

Atualize os repositórios e instale o Python, o Git e o Tesseract (motor de OCR):

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

O OCR do quadro de investigação usa o **Tesseract**, que é um programa do sistema (não uma biblioteca Python). Instale o motor e os pacotes de idioma usados pelo projeto — português, inglês e japonês:

```bash
sudo apt install -y tesseract-ocr tesseract-ocr-por tesseract-ocr-eng tesseract-ocr-jpn
```

Confirme que os três idiomas ficaram disponíveis:

```bash
tesseract --list-langs
```

Você deve ver `por`, `eng` e `jpn` na lista. Se algum faltar, o OCR vai falhar reclamando do idioma ausente.

> **Por que isso é separado do `requirements.txt`:** o `pip` instala apenas a biblioteca `pytesseract` (a "ponte" Python). O binário do Tesseract e os idiomas vêm pelo `apt`. Esquecer este passo é o erro mais comum — resulta em `TesseractNotFoundError`.

---

### Parte 1 — Backend (Django + API)

Clone o repositório e entre na pasta raiz do projeto (a que contém `manage.py`):

```bash
git clone <url-do-seu-repositorio> DetectiveLab
cd DetectiveLab
```

Crie e ative um ambiente virtual Python (isola as dependências do projeto):

```bash
python3 -m venv venv
source venv/bin/activate
```

Com o ambiente ativo (você verá `(venv)` no terminal), instale as dependências:

```bash
pip install -r requirements.txt
```

Aplique as migrações do banco de dados (cria as tabelas, incluindo a de tokens de autenticação da API):

```bash
python manage.py migrate
```

Crie um superusuário para acessar o painel administrativo do Django (necessário para cadastrar os autores do Mural de Casos, que só o admin gerencia):

```bash
python manage.py createsuperuser
```

Inicie o servidor:

```bash
python manage.py runserver
```

O site web fica disponível em `http://localhost:8000` e a API em `http://localhost:8000/api/`. O painel admin (para cadastrar autores e obras) fica em `http://localhost:8000/admin/`.

**Deixe este terminal aberto** com o servidor rodando.

---

### Parte 2 — App mobile (Ionic)

O app roda sobre Node.js, então precisa de um segundo ambiente. Recomendamos instalar o Node via **nvm** (Node Version Manager), que evita as versões antigas do `apt`:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
```

Feche e reabra o terminal (ou rode `source ~/.bashrc`), depois instale a versão LTS do Node e o Ionic CLI:

```bash
nvm install --lts
npm install -g @ionic/cli
```

Em um **segundo terminal**, entre na pasta do app mobile e instale as dependências:

```bash
cd DetectiveLab/DetectiveLab_Mobile
npm install
```

Inicie o app:

```bash
ionic serve
```

O app abre no navegador em `http://localhost:8100`.

---

### Rodando os dois juntos

A aplicação completa exige os **dois servidores rodando ao mesmo tempo**, em terminais separados:

| Terminal | Pasta | Comando | Porta |
|----------|-------|---------|-------|
| 1 (backend) | raiz do projeto | `python manage.py runserver` | 8000 |
| 2 (app) | `DetectiveLab_Mobile` | `ionic serve` | 8100 |

O app em `localhost:8100` faz requisições para a API em `localhost:8000`. O CORS já está configurado no backend para permitir essa origem.

---

### Rodando o app em um celular real

Ao testar no navegador, `localhost` funciona porque o app e a API estão na mesma máquina. Em um **celular físico**, `localhost` aponta para o próprio celular, não para o seu computador — então a API não é encontrada.

Para resolver, descubra o IP da sua máquina na rede local:

```bash
hostname -I
```

Pegue o primeiro endereço (algo como `192.168.0.10`) e edite `DetectiveLab_Mobile/src/environments/environment.ts`, trocando `localhost` pelo IP:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://192.168.0.10:8000/api',
};
```

O celular e o computador precisam estar na **mesma rede Wi-Fi**. Lembre também de liberar a origem do celular no `CORS_ALLOWED_ORIGINS` e no `ALLOWED_HOSTS` do `settings.py` do Django.

---

### Resolução de problemas

- **`TesseractNotFoundError` ao importar uma imagem:** o binário do Tesseract não foi instalado. Rode o `sudo apt install tesseract-ocr ...` da seção de pré-requisitos.
- **Erro de idioma no OCR (ex: "Failed loading language 'jpn'"):** falta o pacote de idioma. Instale `tesseract-ocr-jpn` (ou o idioma indicado) e confira com `tesseract --list-langs`.
- **App não conecta à API / erro de CORS no console do navegador:** confirme que o backend está rodando na porta 8000 e que `corsheaders` está configurado no `settings.py` com `localhost:8100` em `CORS_ALLOWED_ORIGINS`.
- **`ionic: command not found`:** o Ionic CLI não foi instalado globalmente ou o terminal não recarregou o ambiente do nvm. Rode `npm install -g @ionic/cli` e reabra o terminal.
- **Mural de Casos vazio:** os autores são cadastrados apenas pelo admin. Acesse `http://localhost:8000/admin/`, faça login com o superusuário e cadastre autores e obras.

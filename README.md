# 💌  TelePostKeeper Bot (with GitHub Actions Runner)

This repository hosts a GitHub Actions workflow to automate tasks for TelePostKeeper (TPK), a tool for managing and posting content to Telegram channels efficiently. The bot is designed to run directly within GitHub Actions, leveraging the platform’s robust environment for scheduling, event-based triggers, and task automation.


## 🚀 Features

 - Automated Scheduling: Runs every 10 minutes by default or on specific triggers like branch pushes or release publications.
 - Content Management: Downloads, processes, and posts content to specified Telegram channels.
 - Encrypted Environment: Secure handling of sensitive data like API tokens and channel configurations.
 - Customizable Workflow: Supports flexible configurations for storage, timeout limits, and more.
 - Frontend Support: Includes a frontend command to preview or manage tasks interactively.
 - Auto-Commit Integration: Automatically commits generated updates (like logs or processed outputs) back to the repository.


## 🛠️ Setup Instructions

1. Create a new repository in your GitHub.

## 2. Define Secrets and Variables

### Required Secrets

Go to your repository’s Settings > Secrets and Variables > Actions, and add the following:
 - TPK_BOT_TOKEN: The Telegram Bot API token.
 - TPK_CHANNELS_IDS_LIST: List of target Telegram channel IDs (1111,2222,333,444).
 - 
### Optional Variables


Add the following in Settings > Secrets and Variables > Actions (Variables):

 - TPK_STORE_DIR: Directory for storing processed data (e.g., data/).


 - TPK_ENCRYPT_AES_KEY_BASE64: A Base64-encoded AES encryption key for secure data handling.
 - TPK_ENCRYPT_AES_IV_BASE64: Initialization Vector for AES encryption (Base64-encoded).
 - TPK_CHANNELS_IDS_LIST_ENCRYPTED: AES-encrypted list of channel IDs (if using encryption).


 - TPK_SKIP_DOWNLOAD_TEXT
 - TPK_SKIP_DOWNLOAD_PHOTO
 - TPK_SKIP_DOWNLOAD_DOCUMENT
 - TPK_SKIP_DOWNLOAD_AUDIO
 - TPK_SKIP_DOWNLOAD_VIDEO
 - TPK_SKIP_DOWNLOAD_VOICE
 - TPK_SKIP_DOWNLOAD_LOCATION
 - TPK_SKIP_DOWNLOAD_STICKER
 - TPK_SKIP_DOWNLOAD_THUMBNAIL



## 3. Configure the Workflow

The bot uses a pre-configured GitHub Actions workflow. The file is located at .github/workflows/tpk-runner.yml. It includes the following triggers:
 - Schedule: Runs every 10 minutes by default.
 - Push: Executes on pushes to the main branch.
 - Release: Triggers when a new release is published.

## 4. Start the Workflow

Commit the changes to your repository and push them to GitHub. The workflow will start running automatically based on the defined triggers.

## 🔄 GitHub Actions Workflow

Below is the full workflow used to run the bot:


```yaml
name: 💎 tpk-runner
run-name: 🚀 tpk-runner (${{ github.actor }}) 🚀

on:
  schedule:
    - cron: '*/10 * * * *'  # Runs every 10 minutes
  push:
    branches:
      - main  # Trigger on pushes to the main branch
  release:
    types: [published]  # Trigger on new releases

permissions:
  contents: write  # Required for auto-commit

jobs:
  tpk-runner:
    runs-on: ubuntu-latest
    env:
      TPK_BOT_TOKEN: ${{ secrets.TPK_BOT_TOKEN }}
      TPK_ENCRYPT_AES_KEY_BASE64: ${{ secrets.TPK_ENCRYPT_AES_KEY_BASE64 }}
      TPK_CHANNELS_IDS_LIST: ${{ vars.TPK_CHANNELS_IDS_LIST }}
      TPK_CHANNELS_IDS_LIST_ENCRYPTED: ${{ vars.TPK_CHANNELS_IDS_LIST_ENCRYPTED }}
      TPK_ENCRYPT_AES_IV_BASE64: ${{ vars.TPK_ENCRYPT_AES_IV_BASE64 }}
      TPK_SKIP_DOWNLOAD_BIGGER: ${{ vars.TPK_SKIP_DOWNLOAD_BIGGER }}
      TPK_STORE_DIR: ${{ vars.TPK_STORE_DIR }}
    steps:
      - name: 👋 Checkout repository
        uses: actions/checkout@v4

      - name: 🐍 Set up Python environment
        uses: actions/setup-python@v3
        with:
          python-version: '3.x'

      - name: 🔄 Install TPK
        run: pip install telepostkeeper

      - name: 🔄 Install process-time-killer
        run: pip install process-time-killer

      - name: 📡 Listening
        run: timekiller "telepostkeeper" --timeout 30

      - name: 🖼 Frontend
        run: telepostkeeper-frontend

      - name: Get current date-time
        run: echo "COMMIT_MESSAGE=$(date '+%Y-%m-%d %H:%M:%S')" >> $GITHUB_ENV

      - name: 💾 Git Auto Commit
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: ${{ env.COMMIT_MESSAGE }}
```


## 🧰 Tools Used

 - GitHub Actions: Automates tasks and triggers events.
 - TelePostKeeper: The core tool for managing Telegram channel content.
 - Process-Time-Killer: Monitors and manages process execution time.
 - Python: The runtime environment for the bot.



## 📋 Notes

 - Timeout Management: Customize the timeout value for timekiller as needed.
 - Storage: Files are stored in the specified directory (TPK_STORE_DIR). Ensure enough storage is available.


## 🛡️ Security

 - Use GitHub Secrets to store sensitive credentials like TPK_BOT_TOKEN and encryption keys.
 - Avoid hardcoding secrets in your workflow files or scripts.


## 📝 License

This project is licensed under the MIT License.

## Todo

- Number of posts at every parent item

# source this file if you want your prompt to show your
# git branch while developing yac
source /etc/bash_completion.d/git-prompt
PS1="[\[\033[32m\]\w]\[\033[0m\]\$(__git_ps1)\n\[\033[1;36m\]\u\[\033[32m\]$ \[\
\033[0m\]"

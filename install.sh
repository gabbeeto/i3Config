# install stuff
sudo pacman -S keyd --noconfirm --needed
sudo pacman -S yt-dlp --noconfirm --needed
sudo pacman -S qutebrowser --noconfirm --needed

sudo pacman -S luanti --noconfirm --needed
sudo pacman -S kitty --noconfirm --needed

sudo pacman -S gimp --noconfirm --needed
sudo pacman -S pinta --noconfirm --needed
sudo pacman -S xclip --noconfirm --needed

sudo pacman -S libreoffice --noconfirm --needed

# video editing
sudo pacman -S flowblade --noconfirm --needed

# diagram
sudo pacman -S d2 --noconfirm --needed

# drawing program
sudo pacman -S git --noconfirm --needed

# best terminal file manager and dependencies
sudo pacman -S yazi  7zip  poppler fd ripgrep  zoxide resvg imagemagick cargo --noconfirm --needed

# for c++ and godot
sudo pacman -S clang scons python3 --noconfirm --needed

# apps for that I use daily
sudo pacman -S curl ffmpeg unzip go helix tmux npm nodejs python-pip python-pipx python  fzf arch-wiki-docs mpv man-db man-pages less --noconfirm --needed


#prism launcher for minecraft
sudo pacman -S prismlauncher --needed --noconfirm



# dependencies for raylib and raylib
sudo pacman -S cmake libx11 libxcursor libxinerama libxrandr  glfw-x11 base-devel raylib --noconfirm --needed



npm-install-if-needed() {
    if ! npm list -g "$1" --depth=0 | grep -q "$1"; then
        sudo npm install -g "$1" --no-fund --no-audit
    else
        sudo npm update -g "$1" --no-fund --no-audit
    fi
}

 # install language servers for helix
npm-install-if-needed vscode-langservers-extracted
npm-install-if-needed @olrtg/emmet-language-server
npm-install-if-needed typescript
npm-install-if-needed typescript-language-server

sudo pacman -S python-lsp-server --noconfirm --needed
sudo pacman -S lua-language-server --noconfirm --needed

# install ripdrag
cargo install ripdrag

# for godot language server
sudo pacman -S nmap --needed --noconfirm
pipx install "gdtoolkit==4.*"
pipx upgrade "gdtoolkit==4.*"

# fuse2 for appimages
sudo pacman -S fuse2 --noconfirm --needed





sudo systemctl enable keyd --now
sudo systemctl start keyd

echo "alias hx='helix'" >> ~/.bashrc

echo "alias download='yt-dlp -f \"bestvideo[height<=720]+bestaudio/best[height<=720]\" --embed-subs  --add-metadata --merge-output-format mkv '" >> ~/.bashrc
echo "alias downloadP='yt-dlp -o  \"%(playlist_index)03d - %(title)s.%(ext)s\" -f \"bestvideo[height<=720]+bestaudio/best[height<=720]\" --embed-subs --add-metadata --merge-output-format mkv '" >> ~/.bashrc
echo "export EDITOR=\"helix\"" >> ~/.bashrc
echo "export PATH=\$PATH:~/.cargo/bin" >> ~/.bashrc
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
echo 'export PATH="$PATH:$HOME/software/"' >> ~/.bashrc


# I use the y command to navegate through yazi
echo "function y() {
	local tmp=\"\$(mktemp -t \"yazi-cwd.XXXXXX\")\" cwd
	yazi \"\$@\" --cwd-file=\"\$tmp\"
	IFS= read -r -d '' cwd < \"\$tmp\"
	[ -n \"\$cwd\" ] && [ \"\$cwd\" != \"\$PWD\" ] && builtin cd -- \"\$cwd\"
	rm -f -- \"\$tmp\"
}" >> ~/.bashrc




sudo keyd reload

git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.editor "helix"

source ~/.bashrc

git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

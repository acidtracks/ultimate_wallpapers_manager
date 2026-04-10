# Maintainer: acidtracks
pkgname=ultimate-wallpapers-manager
pkgver=0.1.0b1
pkgrel=1
pkgdesc="Gestionnaire de fonds d'écran intelligent basé sur les médias et jeux actifs (Hyprland/Wayland)"
arch=('any')
license=('MIT')
depends=(
  'python>=3.11'
  'playerctl'
)
makedepends=(
  'python-build'
  'python-installer'
  'python-setuptools'
)
optdepends=(
  'swww: backend wallpaper Wayland natif (défaut)'
  'awww: fork compatible swww (alternative)'
  'hyprpaper: backend alternatif pour Hyprland'
  'waypaper: backend alternatif générique Wayland/X11'
  'lutris: intégration bibliothèque de jeux Lutris'
  'steam: intégration bibliothèque Steam'
)
install=$pkgname.install
source=()
sha256sums=()

build() {
  cd "$startdir"
  python -m build --wheel --no-isolation
}

package() {
  cd "$startdir"
  python -m installer --destdir="$pkgdir" dist/*.whl

  # Units systemd utilisateur
  local _systemd="$pkgdir/usr/lib/systemd/user"
  install -Dm644 systemd/swww-daemon.service  "$_systemd/swww-daemon.service"
  install -Dm644 systemd/uwm-watcher.service "$_systemd/uwm-watcher.service"
  install -Dm644 systemd/uwm-rotate.service  "$_systemd/uwm-rotate.service"
  install -Dm644 systemd/uwm-rotate.timer    "$_systemd/uwm-rotate.timer"

  # Config exemple
  install -Dm644 config.example.toml \
    "$pkgdir/usr/share/doc/$pkgname/config.example.toml"
}

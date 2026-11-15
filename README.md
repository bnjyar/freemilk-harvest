# freemilk-harvest

Repo sekali pakai: jalankan FreeMilk.app di GitHub Actions macOS runner (gratis), ambil
`access_token` + `refresh_token` dari keychain, lalu semua request AI jalan dari Windows.

## Cara
1. Buat repo kosong di GitHub (boleh private) + PAT classic dengan scope `repo` + `workflow`.
2. Push folder ini, lalu:
   `gh workflow run mac-harvest.yml -R <user>/<repo>`  (atau Actions > mac-harvest > Run workflow)
3. Workflow membuka sesi tmate; `ssh <token>@nyc1.tmate.io` untuk masuk ke runner.
4. Di runner:
   `open -a FreeMilk` lalu `screencapture -x /tmp/s.jpg` (kirim base64 ke layar) untuk lihat UI.
5. Setelah login:
   `security find-generic-password -s com.neelmakhecha.milq.auth -w`
   `security find-generic-password -s com.neelmakhecha.milq.refreshToken -w`

## Yang perlu disiapkan operator
- GitHub PAT (repo + workflow).
- Akun Google untuk login di app, plus kode TOTP kalau ada 2FA (diminta live, 30 detik).

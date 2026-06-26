#!/usr/bin/env python3
"""
Email-to-Post WordPress Script
Mengirim artikel Markdown ke WordPress via Email-to-Post feature
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class WordPressEmailPoster:
    """Send articles to WordPress via Email-to-Post."""
    
    def __init__(self, 
                 smtp_server: str = "smtp.gmail.com",
                 smtp_port: int = 587,
                 sender_email: str = None,
                 sender_password: str = None):
        """
        Initialize email poster.
        
        Args:
            smtp_server: SMTP server (default: Gmail)
            smtp_port: SMTP port (default: 587)
            sender_email: Your email address
            sender_password: Your email password or app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.wordpress_email = "xuxa564muxo@post.wordpress.com"
    
    def read_markdown_article(self, file_path: str) -> dict:
        """Read markdown article and extract metadata."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse title (first H1)
        title = ""
        body = content
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                body = '\n'.join(lines[i+1:])
                break
        
        return {
            'title': title,
            'body': body,
            'file_path': file_path
        }
    
    def format_email_body(self, article: dict) -> str:
        """Format article for WordPress Email-to-Post."""
        # WordPress Email-to-Post format:
        # Subject: Title
        # Body: Content
        
        formatted_body = article['body'].strip()
        
        # Remove extra metadata at end
        if '**Dibuat oleh:**' in formatted_body:
            formatted_body = formatted_body.split('**Dibuat oleh:**')[0].strip()
        
        return formatted_body
    
    def send_to_wordpress(self, article: dict, 
                         status: str = "publish",
                         category: str = "Agribisnis"):
        """
        Send article to WordPress via Email-to-Post.
        
        Args:
            article: Article dict with title and body
            status: Post status (publish/draft/private)
            category: Post category
        """
        try:
            # Format email
            subject = article['title']
            body = self.format_email_body(article)
            
            # Add WordPress metadata as email body format
            # Some WordPress setups support tags in body
            email_content = body + f"""

---

**Status:** {status}
**Kategori:** {category}
**Posted at:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Source:** adioranye Blog Automation
            """
            
            # Create email
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = self.wordpress_email
            
            # Attach body as plain text
            part1 = MIMEText(email_content, "plain", "utf-8")
            message.attach(part1)
            
            # Send email
            print(f"\n📧 Mengirim email ke WordPress...")
            print(f"   To: {self.wordpress_email}")
            print(f"   Subject: {subject}")
            print(f"   Status: {status}")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            print(f"✅ Email terkirim ke WordPress!")
            print(f"   Artikel akan di-post dalam beberapa menit")
            return True
            
        except Exception as e:
            print(f"❌ Error mengirim email: {e}")
            print(f"\n📌 Tips:")
            print(f"   1. Jika pakai Gmail, gunakan App Password")
            print(f"   2. Aktifkan 'Less Secure Apps' di account settings")
            print(f"   3. Pastikan Email-to-Post aktif di WordPress")
            return False
    
    def send_article_from_file(self, file_path: str,
                               sender_email: str = None,
                               sender_password: str = None,
                               status: str = "publish"):
        """Send article from file to WordPress."""
        if not os.path.exists(file_path):
            print(f"❌ File tidak ditemukan: {file_path}")
            return False
        
        # Update credentials if provided
        if sender_email:
            self.sender_email = sender_email
        if sender_password:
            self.sender_password = sender_password
        
        # Validate credentials
        if not self.sender_email or not self.sender_password:
            print(f"❌ Email dan password diperlukan")
            print(f"   Gunakan: send_article_from_file(file, sender_email='...', sender_password='...')")
            return False
        
        # Read and send
        article = self.read_markdown_article(file_path)
        return self.send_to_wordpress(article, status=status)


def main():
    """Interactive script untuk send artikel."""
    print("\n" + "="*70)
    print("📧 WordPress Email-to-Post Sender")
    print("="*70)
    
    # Input email credentials
    print("\n🔐 Masukkan kredensial email:")
    sender_email = input("Email address (Gmail/Yahoo/etc): ").strip()
    sender_password = input("Password atau App Password: ").strip()
    
    if not sender_email or not sender_password:
        print("❌ Email dan password harus diisi")
        return
    
    # Input article file
    print("\n📄 Pilih artikel yang akan dikirim:")
    article_file = input("Path ke file (default: artikel_peternakan.md): ").strip()
    article_file = article_file or "artikel_peternakan.md"
    
    if not os.path.exists(article_file):
        print(f"❌ File tidak ditemukan: {article_file}")
        return
    
    # Input post status
    print("\n📝 Status post:")
    print("   1. publish (langsung tayang)")
    print("   2. draft (draft, belum tayang)")
    print("   3. private (private, hanya pemilik)")
    
    status_choice = input("Pilih (default: 1): ").strip() or "1"
    status_map = {"1": "publish", "2": "draft", "3": "private"}
    status = status_map.get(status_choice, "publish")
    
    # Send
    poster = WordPressEmailPoster(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        sender_email=sender_email,
        sender_password=sender_password
    )
    
    result = poster.send_article_from_file(
        article_file,
        sender_email=sender_email,
        sender_password=sender_password,
        status=status
    )
    
    if result:
        print("\n✅ Proses selesai!")
        print("   Cek email WordPress Anda dalam 5-10 menit")
    else:
        print("\n❌ Gagal mengirim artikel")


if __name__ == "__main__":
    main()

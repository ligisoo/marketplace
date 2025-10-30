"""Create superuser and approve pending tips"""
from django.contrib.auth import get_user_model
from apps.tips.models import Tip

User = get_user_model()

print("=" * 60)
print("ADMIN USER SETUP")
print("=" * 60)

# Create superuser
phone = input("\nEnter admin phone number (e.g., 0712345678): ").strip()
username = input("Enter admin username (optional, press Enter to skip): ").strip() or None
password = input("Enter admin password: ").strip()

if User.objects.filter(phone_number=phone).exists():
    print(f"\n✗ User with phone {phone} already exists!")
    user = User.objects.get(phone_number=phone)
    print(f"  Making {user.phone_number} an admin...")
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print("✓ User is now an admin!")
else:
    user = User.objects.create_superuser(
        phone_number=phone,
        username=username,
        password=password
    )
    print(f"\n✓ Admin user created: {user.phone_number}")
    print(f"  Username: {user.username or 'N/A'}")
    print(f"  Staff: {user.is_staff}")
    print(f"  Superuser: {user.is_superuser}")

print("\n" + "=" * 60)
print("PENDING TIPS")
print("=" * 60)

# Show pending tips
pending_tips = Tip.objects.filter(status='pending_approval')
print(f"\nFound {pending_tips.count()} pending tips:\n")

for tip in pending_tips:
    print(f"  • Bet Code: {tip.bet_code}")
    print(f"    Tipster: {tip.tipster.username or tip.tipster.phone_number}")
    print(f"    Odds: {tip.odds}")
    print(f"    Price: KES {tip.price}")
    print(f"    Created: {tip.created_at.strftime('%Y-%m-%d %H:%M')}")
    print()

print("\nTo approve tips:")
print("1. Access Django Admin: http://localhost:8000/admin/")
print(f"2. Login with: {phone}")
print("3. Go to 'Tips' section")
print("4. Filter by 'Pending approval'")
print("5. Select tips and choose 'Approve selected tips'")
print("\nOR run: python manage.py approve_gladys_tips")

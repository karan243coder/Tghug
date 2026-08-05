# 🎯 Step-by-Step Guide (Hindi)

## Pehle Samjho Kya Hai Ye

Ye bot tumhari photo edit karta hai AI se. Face bilkul same rehta hai!

**Kaise kaam karta hai:**
1. Tum photo bhejte ho Telegram pe
2. Tum prompt likhte ho (kya change karna hai)
3. Bot Hugging Face FREE API use karta hai
4. Edited photo wapas aati hai

**Important:** Koi paisa nahi lagta! Sab FREE hai!

---

## 📋 Kya Chahiye?

1. ✅ Telegram Account (sabke paas hota hai)
2. ✅ Internet Connection
3. ✅ 10 minute ka time

---

## 🚀 STEP 1: Telegram Bot Banao

### 1.1 Telegram kholo

Phone ya desktop pe Telegram app kholo.

### 1.2 BotFather dhundho

Search karo: `@BotFather`

Ya click karo: https://t.me/BotFather

### 1.3 New Bot banao

BotFather ko ye message bhejo:

```
/newbot
```

### 1.4 Naam do

Puchega "What name do you want for your bot?"

Kuch bhi likho, jaise:
```
My Image Editor
```

### 1.5 Username do

Puchega "What username do your bot want?"

Username hona chahiye jo 'bot' se end ho, jaise:
```
my_image_editor_bot
```

### 1.6 Token Copy Karo

Ab tumhe ek TOKEN milega, jaise:

```
7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**YE BAHUT ZAROORI HAI - COPY KARO AUR SAFE RAKHO!**

> ⚠️ Kisi ko mat dena ye token!

---

## 🚀 STEP 2: Hugging Face FREE Token Lo

### 2.1 Account Banao (FREE)

Jaao: https://huggingface.co/join

- Email daalo
- Username do
- Password do
- "Create Account" pe click karo

### 2.2 Email Verify Karo

Email pe ek link aayega. Click karo.

### 2.3 Token Banao

Jaao: https://huggingface.co/settings/tokens

"New token" pe click karo.

**Settings:**
- Name: `telegram-bot`
- Role: `Read`

"Generate token" pe click karo.

### 2.4 Token Copy Karo

Token milega, jaise:

```
hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**COPY KARO AUR SAFE RAKHO!**

> ✅ Ye token FREE hai. Koi charge nahi lagega!

---

## 🚀 STEP 3: Koyeb pe Deploy Karo

### 3.1 Koyeb Account Banao (FREE)

Jaao: https://app.koyeb.com/signup

- GitHub ya email se signup karo
- Email verify karo

### 3.2 Secrets Set Karo

Koyeb dashboard pe jaao.

Left menu mein "Secrets" pe click karo.

**Secret 1:**
- "Create Secret" pe click karo
- Name: `TELEGRAM_BOT_TOKEN`
- Value: (Step 1 ka token paste karo)
- Save karo

**Secret 2:**
- "Create Secret" pe click karo
- Name: `HUGGINGFACE_TOKEN`
- Value: (Step 2 ka token paste karo)
- Save karo

### 3.3 App Create Karo

1. Dashboard pe "Create App" pe click karo

2. **Deployment method choose karo:**
   
   **Option A: GitHub se (Recommended)**
   - Pehle ye repo GitHub pe upload karo
   - "GitHub" select karo
   - Repository choose karo
   - Branch: `main`
   
   **Option B: Docker image se**
   - "Docker" select karo
   - Image: `your-dockerhub-username/telegram-image-editor`

3. **Instance Type:**
   - `Nano` select karo (512MB RAM - FREE!)

4. **Environment Variables:**
   
   Click "Add environment variable"
   
   **Variable 1:**
   - Name: `TELEGRAM_BOT_TOKEN`
   - Type: `Secret`
   - Select: `TELEGRAM_BOT_TOKEN`
   
   **Variable 2:**
   - Name: `HUGGINGFACE_TOKEN`
   - Type: `Secret`
   - Select: `HUGGINGFACE_TOKEN`

5. **Deploy:**
   - "Deploy" pe click karo

### 3.4 Wait Karo

2-3 minute mein bot start ho jayega!

Logs dekhne ke liye:
- Dashboard → App → Logs

---

## 🎉 STEP 4: Bot Use Karo!

### 4.1 Bot Dhundho

Telegram pe search karo apne bot ka username.

Example: `@my_image_editor_bot`

### 4.2 Start Karo

```
/start
```

### 4.3 Photo Bhejo

Koi bhi photo bhejo jisme face ho.

### 4.4 Prompt Likho

Bot puchega kya change karna hai.

**Examples:**

| Kya Karna Hai | Kya Likho |
|---------------|-----------|
| Background change | "Change background to sunset beach" |
| Painting style | "Make it oil painting style" |
| Sunglasses | "Add cool sunglasses" |
| Hair color | "Change hair color to blonde" |
| Professional | "Make it professional headshot" |

### 4.5 Wait Karo

30-60 second lagenge.

### 4.6 Result!

Edited photo aa jayegi! 🎉

---

## ⚠️ Problems & Solutions

### Problem: "Model is loading"
**Solution:** 2-3 minute wait karo. Pehli baar slow hota hai.

### Problem: "Rate limit exceeded"  
**Solution:** 15-30 minute wait karo. Free tier ka limit hai.

### Problem: Face change ho raha hai
**Solution:** Prompt mein likho: "keep face exactly same, only change background"

### Problem: Bot reply nahi de raha
**Solution:** 
1. Koyeb logs check karo
2. Tokens sahi hain verify karo
3. Bot restart karo Koyeb se

### Problem: "HUGGINGFACE_TOKEN not set"
**Solution:** Koyeb mein secret sahi set karo (Step 3.2)

---

## 💡 Pro Tips

### Best Photos for Face Consistency:
- ✅ Front-facing photo
- ✅ Good lighting
- ✅ Clear face visible
- ❌ Side profile (avoid)
- ❌ Too dark photo (avoid)

### Best Prompts:
- ✅ "Change background to [X], keep face same"
- ✅ "Add [accessory] on face"
- ✅ "Make it [style], maintain face"
- ❌ "Change everything" (too vague)
- ❌ "Make me look different" (face change hoga)

---

## 📞 Help

Koi problem? 

1. Is file ko dubara padho
2. Koyeb logs check karo
3. Tokens verify karo

---

## ✅ Checklist

- [ ] Telegram Bot Token mila
- [ ] Hugging Face Token mila
- [ ] Koyeb account bana
- [ ] Secrets set kiye
- [ ] App deploy ki
- [ ] Bot start hua
- [ ] Photo bheji
- [ ] Result aaya!

**Sab ho gaya? Badhiya! Ab maze karo! 🎉**

---

**Made with ❤️ | Bilkul FREE!**

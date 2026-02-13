# 📋 Manual Testing Guide - Verify All Requirements

## 🎯 Your Requirements

1. ✅ **Text input** → Bot replies with **text only** (NO voice)
2. ✅ **Voice input** → Bot replies with **text + voice**
3. ✅ **Thinking indicator** → Shows "Thinking..." so user knows bot is working

---

## 🚀 How to Test

### Open the Application

1. Open your browser
2. Go to: **http://localhost:8080**
3. Wait for the page to load

---

## ✅ TEST 1: Text Input (No Voice)

**Purpose**: Verify that typing a question does NOT trigger voice playback

**Steps**:
1. Click in the message input box at the bottom
2. Type: `What is machine learning about?`
3. Press **Enter** or click the **Send** button
4. **Observe**: While waiting, you should see "⏳ Thinking..." with animated dots
5. **Verify**: When the response appears, it should be **TEXT ONLY**
6. **Listen**: NO voice should play automatically

**Expected Result**: ✅
- Thinking indicator appears
- Text response appears
- **NO voice playback**

**If voice plays**: ❌ Test FAILED - The code may not have reloaded

---

## ✅ TEST 2: Voice Input (With Voice)

**Purpose**: Verify that voice input DOES trigger voice playback

**Steps**:
1. Click the **🎤 microphone button** (usually next to the send button)
2. Allow microphone access if prompted
3. Speak clearly: *"What is machine learning?"*
4. The button should show you're recording
5. Click the microphone button again to stop, OR it auto-stops
6. **Observe**: "⏳ Thinking..." indicator appears
7. Wait for transcription and response

**Expected Result**: ✅
- Thinking indicator appears
- Text response appears
- **Voice DOES play** automatically

**If voice doesn't play**: ❌ Test FAILED

---

## ✅ TEST 3: Thinking Indicator

**Purpose**: Verify that users see clear feedback while bot is processing

**Steps**:
1. Type any question: `Tell me about the Intelligent Robotics programme`
2. Press Enter
3. **Immediately look** at the chat area

**Expected Result**: ✅
- You should see a message with:
  - 🤖 emoji avatar
  - Three animated dots (● ● ●)
  - Text saying "Thinking..."
  - Italic, gray text style
- This disappears when the real answer arrives

**If you don't see it**: ❌ Test FAILED - Indicator may be too fast or not working

---

## ✅ TEST 4: RAG System Accuracy

**Purpose**: Verify that the chatbot gives accurate, relevant answers

**Test Queries**:

### Query 1: Programme Overview
```
Tell me about the Intelligent Robotics programme
```

**Expected**: 
- Mentions "Intelligent Robotics"
- Mentions "programme" or "program"
- Describes robotic/automation/electronics content
- Long answer (100+ words)

### Query 2: Term Structure
```
What subjects are in Year 2 Trimester 1?
```

**Expected**:
- Lists multiple course codes
- Mentions "Year 2" or "Trimester 1"
- Shows specific courses

### Query 3: Alias Resolution
```
What is deep learning about?
```

**Expected**:
- Resolves "deep learning" to a course code (e.g., ACE6333)
- Gives details about that course
- Mentions deep learning concepts

### Query 4: Course Code
```
What is ACE6313?
```

**Expected**:
- Returns information about ACE6313
- Mentions "Machine Learning"
- Gives course details

---

## 📊 Results Checklist

After testing, fill this out:

| Test | Requirement | Status | Notes |
|------|-------------|--------|-------|
| 1 | Text input → No voice | ☐ PASS ☐ FAIL | |
| 2 | Voice input → With voice | ☐ PASS ☐ FAIL | |
| 3 | Thinking indicator appears | ☐ PASS ☐ FAIL | |
| 4a | Programme query accurate | ☐ PASS ☐ FAIL | |
| 4b | Term structure accurate | ☐ PASS ☐ FAIL | |
| 4c | Alias resolution works | ☐ PASS ☐ FAIL | |
| 4d | Course code detection works | ☐ PASS ☐ FAIL | |

---

## 🔍 Troubleshooting

### Issue: Voice always plays (even for text input)
**Cause**: Old code is cached in browser
**Fix**: 
1. Hard refresh: **Ctrl + Shift + R** (Windows) or **Cmd + Shift + R** (Mac)
2. Or clear browser cache
3. Reload the page

### Issue: No voice plays at all
**Cause**: Browser voice synthesis disabled or voice settings off
**Fix**:
1. Check browser allows speech synthesis
2. Click settings gear icon in chat
3. Verify "Auto-play voice" is checked

### Issue: Thinking indicator too fast to see
**This is OK!** It means the server is responding quickly. Try:
1. Ask a more complex question
2. Or watch closely right after pressing Enter

### Issue: Answers are short/irrelevant
**Cause**: Structure index may still be building
**Fix**:
1. Wait 30 seconds
2. Try again
3. Check server logs for "Structure index rebuilt: 27 vectors"

---

## ✅ Success Criteria

**ALL of these should be TRUE**:

1. ✅ Typing questions does NOT play voice
2. ✅ Using voice button DOES play voice
3. ✅ "Thinking..." indicator appears
4. ✅ Answers about programmes are relevant
5. ✅ Answers about courses are accurate
6. ✅ "machine learning" resolves to course code
7. ✅ Course codes like ACE6313 are recognized

**If 6 or 7 out of 7 pass**: 🎉 **REQUIREMENTS MET!**

---

## 📸 What to Look For

### Thinking Indicator (Example):
```
╔════════════════════════════════════════╗
║ 🤖                                     ║
║ ⚫ ⚫ ⚫ Thinking...                     ║
║ (italic, gray text)                    ║
╚════════════════════════════════════════╝
```

### Voice Settings (Top right):
```
⚙️ Settings
  Voice Profile: [ Female EN ▼ ]
  ✓ Auto-play voice responses
```

### Voice Button States:
- **Normal**: 🎤 (gray)
- **Recording**: 🎤 (red, pulsing)
- **Processing**: 🎤 (disabled while thinking)

---

## 💡 Tips

- **Test voice LAST** - Text input is easier to verify first
- **Watch the indicator** - Look for "Thinking..." right after sending
- **Check browser console** - Press F12 to see any JavaScript errors
- **Try different queries** - Mix programme, structure, and course questions

---

## 📝 Report Your Results

After testing, note:
1. Which tests passed ✅
2. Which tests failed ❌
3. Any unexpected behavior
4. Screenshots if possible

This helps verify that ALL your requirements have been met!

# ⚙️ Configuration - The AI's Personality & Behavior

This folder contains the **instructions and personality** that make the AI behave like a knowledgeable, helpful tire sales expert instead of a generic chatbot.

## 📁 What's in This Folder

### 🧠 **prompt.py** - The AI's Instructions
**What it does:** This file contains all the instructions that tell the AI how to behave, what to say, and how to help customers find the perfect tires.

**In simple terms:** This is like the AI's job description and training manual - it tells the AI to act like a professional tire salesperson who really cares about helping customers.

## 🎯 What the AI Is Told to Do

### **The AI's Mission:**
The AI has two main goals:
1. **Get customers the perfect tire recommendation as quickly as possible**
2. **Make sure customers are completely satisfied with the experience**

### **The AI's Personality:**
The AI is instructed to be:
- **Knowledgeable** - Knows about different tire types, brands, and performance
- **Helpful** - Provides guidance and explains things clearly
- **Efficient** - Doesn't waste time with unnecessary questions
- **Professional** - Maintains a helpful, trustworthy tone
- **Adaptive** - Adjusts to the customer's knowledge level

## 🧠 How the AI Thinks

### **The "Inside Out" Approach:**
The AI uses an internal thinking process with different "emotions" that help it make decisions:

- **Logic:** Analyzes facts and looks up information when needed
- **Empathy:** Focuses on how the customer feels and what they need
- **Urgency:** Tries to be efficient and not waste the customer's time
- **Curiosity:** Asks good questions to understand the customer better
- **Joy:** Celebrates progress and builds positive feelings
- **Fear:** Identifies potential problems or misunderstandings
- **Productivity:** Avoids repetitive questions and seeks efficiency

### **Example of AI Thinking:**
```
Customer: "I need tires for my Honda Civic"

Logic: "Honda Civic is a compact car, need to consider size and performance"
Empathy: "Customer might not know their tire size, should offer help"
Urgency: "Get to the recommendation quickly"
Curiosity: "Need to know year, driving habits, preferences"
Productivity: "Don't ask for make/model again, they already said Honda Civic"
```

## 📝 How the AI Creates Forms

### **Form Creation Rules:**
The AI is told to create forms that:
- Appear naturally within the conversation
- Have clear, friendly labels
- Include helpful examples and placeholders
- Are never required (so customers can skip if they don't know)
- Provide multiple choice options when appropriate

### **Available Form Types:**
- **Text fields:** For things like vehicle make, model, preferences
- **Dropdown menus:** For choices like driving conditions, tire types
- **Checkboxes:** For multiple selections like features or priorities
- **Year fields:** Specifically for vehicle years

### **Example Form Creation:**
```
AI Response: "Let me help you find the perfect tires! I need to know about your vehicle:

{create_text_field(name="make", label="Vehicle Make", placeholder="e.g., Honda, Toyota")}
{create_text_field(name="model", label="Vehicle Model", placeholder="e.g., Civic, Camry")}
{create_year_field(name="year", label="Vehicle Year")}

Once you provide these details, I can look up the exact tire specifications for your vehicle."
```

## 🔄 The AI's Conversation Flow

### **Step 1: Understanding Needs**
- Greet the customer warmly
- Understand what they're looking for
- Create forms to gather basic information

### **Step 2: Gathering Details**
- Ask about vehicle information
- Understand driving habits and conditions
- Learn about preferences and priorities

### **Step 3: Making Recommendations**
- Provide specific tire recommendations
- Explain why each option is good
- Consider budget and preferences

### **Step 4: Supporting Decisions**
- Answer questions about recommendations
- Help with final decision making
- Provide additional information as needed

## 🎨 What Makes This AI Special

### **It's Like a Real Expert:**
- Knows about different tire types and when to recommend them
- Understands driving conditions and their impact on tire choice
- Can explain technical details in simple terms
- Provides personalized recommendations

### **It's Efficient and Helpful:**
- Remembers what you've already told it
- Doesn't ask the same questions twice
- Looks up information when it can
- Adapts to your knowledge level

### **It Creates Natural Conversations:**
- Forms appear within the conversation, not as separate screens
- Explains why it needs each piece of information
- Provides helpful examples and guidance
- Maintains a professional but friendly tone

## 🚀 Customizing the AI

### **Changing the AI's Personality:**
1. Edit the personality instructions in `prompt.py`
2. Adjust the tone and style of responses
3. Modify how the AI approaches different situations

### **Adding New Form Types:**
1. Add the form function to the instructions
2. Update the AI's knowledge about available forms
3. Test with different customer scenarios

### **Improving Recommendations:**
1. Update the AI's knowledge about tire types and performance
2. Refine the recommendation logic
3. Add new factors to consider

## 🔍 Troubleshooting AI Behavior

### **AI responses are too generic:**
- Check the personality and mission instructions
- Make sure the AI has clear guidance about its role

### **AI asks repetitive questions:**
- Review the memory and efficiency instructions
- Ensure the AI is told to remember previous information

### **Forms don't appear in conversations:**
- Verify the form creation instructions are included
- Check that the AI knows about available form types

### **AI doesn't sound professional:**
- Review the tone and style instructions
- Adjust the personality guidelines

---

*This configuration makes the AI behave like a knowledgeable, helpful tire expert who really understands customer needs and provides exceptional service.* 
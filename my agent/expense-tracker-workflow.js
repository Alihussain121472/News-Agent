export const meta = {
  name: 'expense-tracker',
  description: 'Track expenses and generate daily reports sent via Gmail',
  phases: ['collect-expenses', 'analyze', 'send-report']
};

const GMAIL_ADDRESS = 'syedali6160@gmail.com';

async function run({ agent, phase }) {

  await phase('collect-expenses', async () => {
    const expenses = await agent({
      name: 'expense-collector',
      prompt: `Check for new expenses from the following sources:
1. Read expenses.json file if it exists in the current directory
2. Look for any expense records added today (${new Date().toISOString().split('T')[0]})

Return a summary of:
- Total expenses found
- Categories
- Individual expense items with: date, amount, category, description

If expenses.json doesn't exist, create a sample structure showing how expenses should be logged.`
    });

    return expenses;
  });

  await phase('analyze', async () => {
    const analysis = await agent({
      name: 'expense-analyzer',
      prompt: `Analyze the expenses collected and create a comprehensive daily report including:

1. **Daily Summary**
   - Total spent today
   - Number of transactions
   - Average transaction amount

2. **Category Breakdown**
   - Spending by category with percentages
   - Top 3 categories

3. **Insights**
   - Compare to previous days if data available
   - Identify unusual spending patterns
   - Budget alerts if any category exceeds typical amounts

4. **Recommendations**
   - Suggestions for reducing expenses
   - Areas of concern

Format the analysis in a clean, professional HTML email format with:
- Clear headings
- Tables for data
- Color-coded categories (green for low, yellow for moderate, red for high spending)
- Charts described in text (since we'll render them later)`
    });

    return analysis;
  });

  await phase('send-report', async () => {
    await agent({
      name: 'email-sender',
      prompt: `Send the daily expense report to ${GMAIL_ADDRESS}.

Use the Gmail API or nodemailer to send an email with:
- Subject: "Daily Expense Report - ${new Date().toLocaleDateString()}"
- HTML formatted body with the analysis from the previous phase
- Professional styling with embedded CSS

Steps:
1. Check if nodemailer is installed (npm list nodemailer)
2. If not installed, install it: npm install nodemailer
3. Create the email configuration (use Gmail SMTP: smtp.gmail.com, port 587)
4. Send the email with the formatted report

IMPORTANT: For Gmail authentication, you'll need:
- An App Password (not your regular Gmail password)
- Guide the user to generate one at: https://myaccount.google.com/apppasswords

If credentials aren't set up, create a .env.example file showing what's needed:
- EMAIL_USER=syedali6160@gmail.com
- EMAIL_APP_PASSWORD=your_app_password_here

Then create the sending script and provide instructions for the user to add their credentials.`
    });
  });
}

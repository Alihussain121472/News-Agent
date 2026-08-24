import nodemailer from 'nodemailer';
import fs from 'fs/promises';
import dotenv from 'dotenv';

dotenv.config();

async function loadExpenses() {
  try {
    const data = await fs.readFile('expenses.json', 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading expenses:', error);
    return { expenses: [], categories: [], budget: {} };
  }
}

function getTodayExpenses(expenses) {
  const today = new Date().toISOString().split('T')[0];
  return expenses.filter(exp => exp.date === today);
}

function analyzeExpenses(todayExpenses, allExpenses, budget) {
  const total = todayExpenses.reduce((sum, exp) => sum + exp.amount, 0);
  const count = todayExpenses.length;
  const average = count > 0 ? total / count : 0;

  // Category breakdown
  const categoryTotals = {};
  todayExpenses.forEach(exp => {
    categoryTotals[exp.category] = (categoryTotals[exp.category] || 0) + exp.amount;
  });

  // Sort categories by amount
  const sortedCategories = Object.entries(categoryTotals)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => ({
      category,
      amount,
      percentage: ((amount / total) * 100).toFixed(1),
      budget: budget[category] || 0
    }));

  return {
    total,
    count,
    average,
    categoryTotals: sortedCategories
  };
}

function generateHTMLReport(analysis, expenses) {
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return `
<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
      padding: 20px;
      margin: 0;
    }
    .container {
      max-width: 600px;
      margin: 0 auto;
      background-color: white;
      border-radius: 10px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      overflow: hidden;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
    }
    .header h1 {
      margin: 0;
      font-size: 28px;
    }
    .header p {
      margin: 10px 0 0 0;
      opacity: 0.9;
    }
    .content {
      padding: 30px;
    }
    .summary-box {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 25px;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin-top: 15px;
    }
    .stat {
      text-align: center;
    }
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: #667eea;
    }
    .stat-label {
      font-size: 12px;
      color: #666;
      margin-top: 5px;
    }
    .section-title {
      font-size: 18px;
      font-weight: bold;
      color: #333;
      margin-bottom: 15px;
      border-bottom: 2px solid #667eea;
      padding-bottom: 8px;
    }
    .category-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      margin-bottom: 10px;
      border-radius: 6px;
      background: #f8f9fa;
    }
    .category-name {
      font-weight: 600;
      color: #333;
    }
    .category-amount {
      font-weight: bold;
      color: #667eea;
    }
    .progress-bar {
      height: 6px;
      background: #e0e0e0;
      border-radius: 3px;
      margin-top: 8px;
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      transition: width 0.3s;
    }
    .expense-list {
      margin-top: 15px;
    }
    .expense-item {
      padding: 12px;
      border-left: 3px solid #667eea;
      background: #f8f9fa;
      margin-bottom: 10px;
      border-radius: 4px;
    }
    .expense-desc {
      font-weight: 600;
      color: #333;
    }
    .expense-details {
      font-size: 13px;
      color: #666;
      margin-top: 5px;
    }
    .expense-amount {
      float: right;
      font-weight: bold;
      color: #667eea;
      font-size: 16px;
    }
    .footer {
      background: #f8f9fa;
      padding: 20px;
      text-align: center;
      color: #666;
      font-size: 13px;
    }
    .alert {
      background: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 12px;
      margin: 15px 0;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>💰 Daily Expense Report</h1>
      <p>${today}</p>
    </div>

    <div class="content">
      <div class="summary-box">
        <div class="section-title">Today's Summary</div>
        <div class="summary-grid">
          <div class="stat">
            <div class="stat-value">₹${analysis.total.toLocaleString()}</div>
            <div class="stat-label">Total Spent</div>
          </div>
          <div class="stat">
            <div class="stat-value">${analysis.count}</div>
            <div class="stat-label">Transactions</div>
          </div>
          <div class="stat">
            <div class="stat-value">₹${Math.round(analysis.average).toLocaleString()}</div>
            <div class="stat-label">Average</div>
          </div>
        </div>
      </div>

      <div class="section-title">📊 Category Breakdown</div>
      ${analysis.categoryTotals.map(cat => `
        <div class="category-item">
          <div>
            <div class="category-name">${cat.category}</div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${cat.percentage}%"></div>
            </div>
          </div>
          <div class="category-amount">₹${cat.amount.toLocaleString()} (${cat.percentage}%)</div>
        </div>
      `).join('')}

      <div class="section-title">📝 Transaction Details</div>
      <div class="expense-list">
        ${expenses.map(exp => `
          <div class="expense-item">
            <span class="expense-amount">₹${exp.amount.toLocaleString()}</span>
            <div class="expense-desc">${exp.description}</div>
            <div class="expense-details">
              ${exp.category} • ${exp.paymentMethod}
            </div>
          </div>
        `).join('')}
      </div>

      ${analysis.total > 2000 ? `
        <div class="alert">
          ⚠️ <strong>High Spending Alert:</strong> Today's expenses exceeded ₹2,000. Consider reviewing your budget.
        </div>
      ` : ''}
    </div>

    <div class="footer">
      Generated by Expense Tracker Agent<br>
      <small>Automated daily report delivered to your inbox</small>
    </div>
  </div>
</body>
</html>
  `;
}

async function sendEmail(htmlContent) {
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_APP_PASSWORD
    }
  });

  const mailOptions = {
    from: `Expense Tracker <${process.env.EMAIL_USER}>`,
    to: process.env.EMAIL_USER,
    subject: `Daily Expense Report - ${new Date().toLocaleDateString()}`,
    html: htmlContent
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    console.log('✅ Email sent successfully:', info.messageId);
    return true;
  } catch (error) {
    console.error('❌ Error sending email:', error);
    return false;
  }
}

async function main() {
  console.log('📊 Loading expenses...');
  const data = await loadExpenses();

  const todayExpenses = getTodayExpenses(data.expenses);
  console.log(`Found ${todayExpenses.length} expenses for today`);

  if (todayExpenses.length === 0) {
    console.log('ℹ️  No expenses recorded for today. Skipping email.');
    return;
  }

  console.log('📈 Analyzing expenses...');
  const analysis = analyzeExpenses(todayExpenses, data.expenses, data.budget);

  console.log('📧 Generating report...');
  const htmlReport = generateHTMLReport(analysis, todayExpenses);

  console.log('📤 Sending email...');
  const success = await sendEmail(htmlReport);

  if (success) {
    console.log('✨ Daily expense report sent successfully!');
  } else {
    console.log('❌ Failed to send report. Please check your email configuration.');
  }
}

main().catch(console.error);

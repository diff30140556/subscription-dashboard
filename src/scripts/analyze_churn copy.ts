import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') });
import { createClient } from '@supabase/supabase-js';

interface Customer {
  customerID: string;
  gender: string;
  SeniorCitizen: number;
  Partner: string;
  Dependents: string;
  tenure: number;
  PhoneService: string;
  MultipleLines: string;
  InternetService: string;
  OnlineSecurity: string;
  OnlineBackup: string;
  DeviceProtection: string;
  TechSupport: string;
  StreamingTV: string;
  StreamingMovies: string;
  Contract: string;
  PaperlessBilling: string;
  PaymentMethod: string;
  MonthlyCharges: number;
  TotalCharges: string | number;
  Churn: string;
}

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL as string;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase environment variables.');
  console.error('Please create a .env.local file with:');
  console.error('NEXT_PUBLIC_SUPABASE_URL=your_supabase_url');
  console.error('NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function analyzeChurnedCustomers() {
  try {
    const { data, error } = await supabase
      .from('churn_customers')
      .select('*')
      .eq('Churn', 'Yes');

    const churnedCustomers = data as Customer[];

    if (error) {
      console.error('Error fetching churned customers:', error);
      return;
    }

    if (!churnedCustomers) {
      console.error('No data returned');
      return;
    }

    console.log(`Total churned customers: ${churnedCustomers.length}`);
    
    // Analyze patterns
    const patterns: {
      [key: string]: Record<string, number>;
    } = {
      gender: {},
      seniorCitizen: {},
      partner: {},
      dependents: {},
      phoneService: {},
      multipleLines: {},
      internetService: {},
      onlineSecurity: {},
      onlineBackup: {},
      deviceProtection: {},
      techSupport: {},
      streamingTV: {},
      streamingMovies: {},
      contract: {},
      paperlessBilling: {},
      paymentMethod: {},
      tenureRanges: { '0-12': 0, '13-24': 0, '25-48': 0, '49+': 0 },
      monthlyChargeRanges: { '0-35': 0, '36-65': 0, '66-95': 0, '96+': 0 }
    };

    churnedCustomers.forEach(customer => {
      // Count categorical variables
      patterns.gender[customer.gender] = (patterns.gender[customer.gender] || 0) + 1;
      patterns.seniorCitizen[customer.SeniorCitizen] = (patterns.seniorCitizen[customer.SeniorCitizen] || 0) + 1;
      patterns.partner[customer.Partner] = (patterns.partner[customer.Partner] || 0) + 1;
      patterns.dependents[customer.Dependents] = (patterns.dependents[customer.Dependents] || 0) + 1;
      patterns.phoneService[customer.PhoneService] = (patterns.phoneService[customer.PhoneService] || 0) + 1;
      patterns.multipleLines[customer.MultipleLines] = (patterns.multipleLines[customer.MultipleLines] || 0) + 1;
      patterns.internetService[customer.InternetService] = (patterns.internetService[customer.InternetService] || 0) + 1;
      patterns.onlineSecurity[customer.OnlineSecurity] = (patterns.onlineSecurity[customer.OnlineSecurity] || 0) + 1;
      patterns.onlineBackup[customer.OnlineBackup] = (patterns.onlineBackup[customer.OnlineBackup] || 0) + 1;
      patterns.deviceProtection[customer.DeviceProtection] = (patterns.deviceProtection[customer.DeviceProtection] || 0) + 1;
      patterns.techSupport[customer.TechSupport] = (patterns.techSupport[customer.TechSupport] || 0) + 1;
      patterns.streamingTV[customer.StreamingTV] = (patterns.streamingTV[customer.StreamingTV] || 0) + 1;
      patterns.streamingMovies[customer.StreamingMovies] = (patterns.streamingMovies[customer.StreamingMovies] || 0) + 1;
      patterns.contract[customer.Contract] = (patterns.contract[customer.Contract] || 0) + 1;
      patterns.paperlessBilling[customer.PaperlessBilling] = (patterns.paperlessBilling[customer.PaperlessBilling] || 0) + 1;
      patterns.paymentMethod[customer.PaymentMethod] = (patterns.paymentMethod[customer.PaymentMethod] || 0) + 1;

      // Tenure ranges
      if (customer.tenure <= 12) patterns.tenureRanges['0-12']++;
      else if (customer.tenure <= 24) patterns.tenureRanges['13-24']++;
      else if (customer.tenure <= 48) patterns.tenureRanges['25-48']++;
      else patterns.tenureRanges['49+']++;

      // Monthly charge ranges
      if (customer.MonthlyCharges <= 35) patterns.monthlyChargeRanges['0-35']++;
      else if (customer.MonthlyCharges <= 65) patterns.monthlyChargeRanges['36-65']++;
      else if (customer.MonthlyCharges <= 95) patterns.monthlyChargeRanges['66-95']++;
      else patterns.monthlyChargeRanges['96+']++;
    });

    // Calculate percentages and display results
    console.log('\n=== CHURN ANALYSIS SUMMARY ===\n');
    
    Object.entries(patterns).forEach(([category, values]) => {
      console.log(`${category.toUpperCase()}:`);
      Object.entries(values).forEach(([key, count]) => {
        const percentage = ((count / churnedCustomers.length) * 100).toFixed(1);
        console.log(`  ${key}: ${count} (${percentage}%)`);
      });
      console.log('');
    });

    // Calculate averages
    const avgTenure = churnedCustomers.reduce((sum, c) => sum + c.tenure, 0) / churnedCustomers.length;
    const avgMonthlyCharges = churnedCustomers.reduce((sum, c) => sum + c.MonthlyCharges, 0) / churnedCustomers.length;
    const avgTotalCharges = churnedCustomers.reduce((sum, c) => sum + parseFloat(String(c.TotalCharges || 0)), 0) / churnedCustomers.length;

    console.log('AVERAGES:');
    console.log(`  Average Tenure: ${avgTenure.toFixed(1)} months`);
    console.log(`  Average Monthly Charges: $${avgMonthlyCharges.toFixed(2)}`);
    console.log(`  Average Total Charges: $${avgTotalCharges.toFixed(2)}`);

  } catch (error) {
    console.error('Analysis failed:', error);
  }
}

analyzeChurnedCustomers();
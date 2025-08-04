'use client';

import React, { useState, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';
import Toast from '@/components/Toast';

// Supabase configuration
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
const supabase = createClient(supabaseUrl, supabaseKey);

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
  TotalCharges: number;
  Churn: string;
}

const GenerateCustomersPanel: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error';
    isVisible: boolean;
  }>({
    message: '',
    type: 'success',
    isVisible: false,
  });

  // Helper functions for random generation
  const randomChoice = (options: string[]): string => {
    return options[Math.floor(Math.random() * options.length)];
  };

  const randomBoolean = (truePercent: number = 50): boolean => {
    return Math.random() * 100 < truePercent;
  };

  const randomFloat = (min: number, max: number): number => {
    return parseFloat((Math.random() * (max - min) + min).toFixed(2));
  };

  const randomInt = (min: number, max: number): number => {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  };

  // Toast helper functions
  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({
      message,
      type,
      isVisible: true,
    });
  };

  const hideToast = () => {
    setToast(prev => ({
      ...prev,
      isVisible: false,
    }));
  };

  // Generate random customerID with new format: [5-digit random number]-[5 uppercase letters]
  const generateCustomerID = (): string => {
    // Generate 5-digit random number (10000-99999)
    const randomNumber = Math.floor(Math.random() * 90000) + 10000;
    
    // Generate 5 random uppercase letters
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    let randomLetters = '';
    for (let i = 0; i < 5; i++) {
      randomLetters += letters[Math.floor(Math.random() * letters.length)];
    }
    
    return `${randomNumber}-${randomLetters}`;
  };

  const generateInternetServiceFeature = (internetService: string): string => {
    if (internetService === 'No') {
      return 'No internet service';
    }
    return randomChoice(['Yes', 'No']);
  };

  const generateMultipleLines = (phoneService: string): string => {
    if (phoneService === 'No') {
      return 'No phone service';
    }
    return randomChoice(['Yes', 'No']);
  };

  // Generate a single customer with realistic data
  const generateCustomer = (): Customer => {
    const customerID = generateCustomerID();
    const gender = randomChoice(['Male', 'Female']);
    const SeniorCitizen = randomBoolean(30) ? 1 : 0;
    const Partner = randomChoice(['Yes', 'No']);
    const Dependents = randomChoice(['Yes', 'No']);
    const tenure = randomInt(0, 72);
    const PhoneService = randomChoice(['Yes', 'No']);
    const MultipleLines = generateMultipleLines(PhoneService);
    const InternetService = randomChoice(['DSL', 'Fiber optic', 'No']);
    
    // Internet-dependent services
    const OnlineSecurity = generateInternetServiceFeature(InternetService);
    const OnlineBackup = generateInternetServiceFeature(InternetService);
    const DeviceProtection = generateInternetServiceFeature(InternetService);
    const TechSupport = generateInternetServiceFeature(InternetService);
    const StreamingTV = generateInternetServiceFeature(InternetService);
    const StreamingMovies = generateInternetServiceFeature(InternetService);
    
    const Contract = randomChoice(['Month-to-month', 'One year', 'Two year']);
    const PaperlessBilling = randomChoice(['Yes', 'No']);
    const PaymentMethod = randomChoice([
      'Electronic check',
      'Mailed check', 
      'Bank transfer (automatic)',
      'Credit card (automatic)'
    ]);
    
    const MonthlyCharges = randomFloat(18.0, 120.0);
    
    // Calculate TotalCharges with some realistic noise
    const baseTotalCharges = MonthlyCharges * tenure;
    const noise = randomFloat(-50, 100); // Small variation
    const TotalCharges = Math.max(0, baseTotalCharges + noise);
    
    // 25-30% churn rate
    const Churn = randomBoolean(27) ? 'Yes' : 'No';

    return {
      customerID,
      gender,
      SeniorCitizen,
      Partner,
      Dependents,
      tenure,
      PhoneService,
      MultipleLines,
      InternetService,
      OnlineSecurity,
      OnlineBackup,
      DeviceProtection,
      TechSupport,
      StreamingTV,
      StreamingMovies,
      Contract,
      PaperlessBilling,
      PaymentMethod,
      MonthlyCharges,
      TotalCharges,
      Churn,
    };
  };

  // Generate 20 random customers
  const generateCustomers = useCallback(() => {
    setIsGenerating(true);
    
    // Simulate brief loading for better UX
    setTimeout(() => {
      const newCustomers: Customer[] = [];
      for (let i = 0; i < 20; i++) {
        newCustomers.push(generateCustomer());
      }
      setCustomers(newCustomers);
      setIsGenerating(false);
    }, 500);
  }, []);

  // Add customers to database
  const addCustomersToDatabase = useCallback(async () => {
    if (customers.length === 0) {
      showToast('No customers to add. Generate customers first.', 'error');
      return;
    }

    setIsAdding(true);

    try {
      // Insert all customers into the database
      const { data, error } = await supabase
        .from('churn_customers')
        .insert(customers);

      if (error) {
        throw error;
      }

      // Show success toast
      showToast(`Successfully added ${customers.length} customers to database!`, 'success');
      
      // Generate fresh customers to prevent duplicate re-insertion
      generateCustomers();

    } catch (error) {
      console.error('Error adding customers to database:', error);
      showToast(`Failed to add customers: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    } finally {
      setIsAdding(false);
    }
  }, [customers, generateCustomers]);

  // Initialize with 20 customers on mount
  React.useEffect(() => {
    generateCustomers();
  }, [generateCustomers]);

  const renderTableContent = () => {
    if (isGenerating) {
      return (
        <tbody>
          {[...Array(20)].map((_, index) => (
            <tr key={index} className="border-b border-gray-200">
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </td>
            </tr>
          ))}
        </tbody>
      );
    }

    return (
      <tbody className="bg-white divide-y divide-gray-200">
        {customers.map((customer, index) => (
          <tr key={customer.customerID} className="hover:bg-gray-50">
            <td className="px-6 py-4 whitespace-nowrap text-xs font-medium text-gray-900">
              {customer.customerID}
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {customer.gender}
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {customer.SeniorCitizen ? 'Yes' : 'No'}
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {customer.tenure} months
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {customer.Contract}
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {customer.InternetService}
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              ${customer.MonthlyCharges.toFixed(2)}
            </td>
            <td className="px-6 py-4 whitespace-nowrap">
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                customer.Churn === 'Yes' 
                  ? 'bg-red-100 text-red-800'
                  : 'bg-green-100 text-green-800'
              }`}>
                {customer.Churn === 'Yes' ? 'Churned' : 'Active'}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Generate Customers</h1>
        <div className="text-sm text-gray-500">
          {customers.length} mock customers generated
          {customers.length > 0 && (
            <div className="text-xs text-gray-400 mt-1">
              Random 5-digit IDs with letters
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button
          onClick={generateCustomers}
          disabled={isGenerating}
          className={`px-6 py-3 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${
            isGenerating
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-500 cursor-pointer'
          }`}
        >
          {isGenerating ? (
            <div className="flex items-center">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Generating...
            </div>
          ) : (
            'Generate Again'
          )}
        </button>
        
        <button
          onClick={addCustomersToDatabase}
          disabled={isAdding || customers.length === 0}
          className={`px-6 py-3 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${
            isAdding || customers.length === 0
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-green-500 hover:bg-green-600 focus:ring-green-500 cursor-pointer'
          }`}
          title={customers.length === 0 ? 'Generate customers first' : 'Add all customers to database'}
        >
          {isAdding ? (
            <div className="flex items-center">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Adding...
            </div>
          ) : (
            `Add Customers (${customers.length})`
          )}
        </button>
      </div>


      {/* Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Customer ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Gender
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Senior
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tenure
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contract
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Internet
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monthly
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            {renderTableContent()}
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Generation Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold text-blue-600">20</div>
            <div className="text-sm text-gray-500">Total Generated</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {customers.filter(c => c.Churn === 'Yes').length}
            </div>
            <div className="text-sm text-gray-500">Churned</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {customers.filter(c => c.Churn === 'No').length}
            </div>
            <div className="text-sm text-gray-500">Active</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {customers.filter(c => c.SeniorCitizen === 1).length}
            </div>
            <div className="text-sm text-gray-500">Senior Citizens</div>
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
        autoHideDuration={3000}
      />
    </div>
  );
};

export default GenerateCustomersPanel;
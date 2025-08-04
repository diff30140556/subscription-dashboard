'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';

// Supabase configuration - Replace with your actual values
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

interface FetchCustomersResult {
  customers: Customer[];
  totalCount: number;
  error: string | null;
}

const ITEMS_PER_PAGE = 20;

const CustomerList: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Helper function to safely parse numeric values
  const parseNumeric = (value: any): number => {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
      const parsed = parseFloat(value);
      return isNaN(parsed) ? 0 : parsed;
    }
    return 0;
  };

  // Function to fetch customers from Supabase
  const fetchCustomers = useCallback(async (
    page: number = 1,
    search: string = ''
  ): Promise<FetchCustomersResult> => {
    try {
      // Calculate offset for pagination
      const from = (page - 1) * ITEMS_PER_PAGE;
      const to = from + ITEMS_PER_PAGE - 1;

      // Build query with pagination
      let query = supabase
        .from('churn_customers')
        .select('*', { count: 'exact' })
        .range(from, to)
        .order('customerID', { ascending: true });

      // Add search filter if search term exists
      if (search.trim()) {
        query = query.ilike('customerID', `%${search.trim()}%`);
      }

      const { data, count, error } = await query;

      if (error) {
        throw error;
      }

      // Process data to ensure numeric fields are properly parsed
      const processedData = (data || []).map(customer => ({
        ...customer,
        MonthlyCharges: parseNumeric(customer.MonthlyCharges),
        TotalCharges: parseNumeric(customer.TotalCharges),
        tenure: parseNumeric(customer.tenure),
        SeniorCitizen: parseNumeric(customer.SeniorCitizen),
      }));

      return {
        customers: processedData,
        totalCount: count || 0,
        error: null,
      };
    } catch (err) {
      console.error('Error fetching customers:', err);
      return {
        customers: [],
        totalCount: 0,
        error: err instanceof Error ? err.message : 'Failed to fetch customers',
      };
    }
  }, []);

  // Load customers data
  const loadCustomers = useCallback(async () => {
    setLoading(true);
    setError(null);

    const result = await fetchCustomers(currentPage, searchTerm);

    setCustomers(result.customers);
    setTotalCount(result.totalCount);
    setError(result.error);
    setLoading(false);
  }, [currentPage, searchTerm, fetchCustomers]);

  // Load customers on component mount and when dependencies change
  useEffect(() => {
    loadCustomers();
  }, [loadCustomers]);

  // Handle search input with debouncing
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      setCurrentPage(1); // Reset to first page when searching
      loadCustomers();
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  // Handle search input change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  // Calculate pagination info
  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE + 1;
  const endIndex = Math.min(currentPage * ITEMS_PER_PAGE, totalCount);

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;

    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

    if (endPage - startPage + 1 < maxPagesToShow) {
      startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return pages;
  };

  const renderTableContent = () => {
    if (loading) {
      return (
        <tbody>
          {[...Array(ITEMS_PER_PAGE)].map((_, index) => (
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
            </tr>
          ))}
        </tbody>
      );
    }

    if (error) {
      return (
        <tbody>
          <tr>
            <td colSpan={7} className="px-6 py-12 text-center">
              <div className="text-red-500 font-medium">Error: {error}</div>
              <button
                onClick={loadCustomers}
                className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 cursor-pointer"
              >
                Retry
              </button>
            </td>
          </tr>
        </tbody>
      );
    }

    if (customers.length === 0) {
      return (
        <tbody>
          <tr>
            <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
              {searchTerm ? `No customers found matching "${searchTerm}"` : 'No customers found'}
            </td>
          </tr>
        </tbody>
      );
    }

    return (
      <tbody className="bg-white divide-y divide-gray-200">
        {customers.map((customer) => (
          <tr key={customer.customerID} className="hover:bg-gray-50">
            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
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
              ${parseNumeric(customer.MonthlyCharges).toFixed(2)}
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              ${parseNumeric(customer.TotalCharges).toFixed(2)}
            </td>
            <td className="px-6 py-4 whitespace-nowrap">
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${customer.Churn === 'Yes'
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

  const renderPagination = () => {
    if (totalPages <= 1) return null;

    return (
      <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
        <div className="flex-1 flex justify-between sm:hidden">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            Previous
          </button>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            Next
          </button>
        </div>
        <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-700">
              Showing <span className="font-medium">{startIndex}</span> to{' '}
              <span className="font-medium">{endIndex}</span> of{' '}
              <span className="font-medium">{totalCount}</span> results
              {searchTerm && (
                <span className="ml-1">
                  for "<span className="font-medium">{searchTerm}</span>"
                </span>
              )}
            </p>
          </div>
          <div>
            <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                <span className="sr-only">Previous</span>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </button>

              {getPageNumbers().map((pageNumber) => (
                <button
                  key={pageNumber}
                  onClick={() => handlePageChange(pageNumber)}
                  className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${pageNumber === currentPage
                    ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50 cursor-pointer'
                    }`}
                >
                  {pageNumber}
                </button>
              ))}

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                <span className="sr-only">Next</span>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </nav>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Customer List</h1>
      </div>

      {/* Search Bar */}
      <div className="max-w-md">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearchChange}
            placeholder="Search by Customer ID..."
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
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
                  Senior Citizen
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tenure
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monthly Charges
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Charges
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            {renderTableContent()}
          </table>
        </div>

        {/* Pagination */}
        {renderPagination()}
      </div>
    </div>
  );
};

export default CustomerList;
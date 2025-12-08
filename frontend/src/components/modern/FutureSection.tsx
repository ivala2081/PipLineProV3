import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import ChatGPTInterface from './ChatGPTInterface';
import { CHATGPT_CONFIG } from '../../config/chatgpt';
import { 
  Sparkles, 
  MessageSquare, 
  Brain, 
  Zap, 
  Shield,
  BarChart3,
  TrendingUp,
  Globe,
  Cpu,
  Database
} from 'lucide-react';

const FutureSection: React.FC = () => {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <Card className="dashboard-card bg-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="dashboard-title text-xl font-bold text-slate-900">
              Future Technologies
            </CardTitle>
            <p className="dashboard-subtitle text-sm text-slate-600">
              AI-powered insights and next-generation features
            </p>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="px-6 pb-4">
            <TabsList className="grid w-full grid-cols-4 bg-slate-100 p-1 rounded-lg">
              <TabsTrigger 
                value="chat" 
                className="flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                <MessageSquare className="w-4 h-4" />
                <span className="hidden sm:inline">Chat</span>
              </TabsTrigger>
              <TabsTrigger 
                value="ai-insights" 
                className="flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                <Brain className="w-4 h-4" />
                <span className="hidden sm:inline">AI Insights</span>
              </TabsTrigger>
              <TabsTrigger 
                value="automation" 
                className="flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                <Zap className="w-4 h-4" />
                <span className="hidden sm:inline">Automation</span>
              </TabsTrigger>
              <TabsTrigger 
                value="security" 
                className="flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                <Shield className="w-4 h-4" />
                <span className="hidden sm:inline">Security</span>
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="chat" className="m-0">
            <div className="px-6 pb-6">
              <ChatGPTInterface 
                apiKey={CHATGPT_CONFIG.API_KEY}
                className="border-0 h-[500px]"
              />
            </div>
          </TabsContent>

          <TabsContent value="ai-insights" className="m-0">
            <div className="px-6 pb-6">
              <div className="space-y-6">
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Brain className="w-8 h-8 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    AI-Powered Business Insights
                  </h3>
                  <p className="text-slate-600 max-w-md mx-auto">
                    Advanced analytics and predictive modeling powered by machine learning algorithms.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <TrendingUp className="w-5 h-5 text-green-600" />
                      <h4 className="font-medium text-slate-900">Revenue Forecasting</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Predict future revenue trends based on historical data and market patterns.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <BarChart3 className="w-5 h-5 text-blue-600" />
                      <h4 className="font-medium text-slate-900">Risk Analysis</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Identify potential risks and opportunities in your transaction patterns.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Globe className="w-5 h-5 text-purple-600" />
                      <h4 className="font-medium text-slate-900">Market Intelligence</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Real-time market analysis and competitive intelligence insights.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Cpu className="w-5 h-5 text-orange-600" />
                      <h4 className="font-medium text-slate-900">Process Optimization</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      AI-driven recommendations for improving operational efficiency.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="automation" className="m-0">
            <div className="px-6 pb-6">
              <div className="space-y-6">
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gradient-to-r from-yellow-100 to-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Zap className="w-8 h-8 text-yellow-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    Smart Automation
                  </h3>
                  <p className="text-slate-600 max-w-md mx-auto">
                    Automate repetitive tasks and workflows to increase productivity and reduce errors.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Database className="w-5 h-5 text-blue-600" />
                      <h4 className="font-medium text-slate-900">Data Processing</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Automated data validation, cleansing, and transformation pipelines.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <TrendingUp className="w-5 h-5 text-green-600" />
                      <h4 className="font-medium text-slate-900">Report Generation</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Automated generation of daily, weekly, and monthly reports.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Shield className="w-5 h-5 text-red-600" />
                      <h4 className="font-medium text-slate-900">Fraud Detection</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Real-time monitoring and automated alerts for suspicious activities.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Globe className="w-5 h-5 text-purple-600" />
                      <h4 className="font-medium text-slate-900">API Integration</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Seamless integration with external services and third-party APIs.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="security" className="m-0">
            <div className="px-6 pb-6">
              <div className="space-y-6">
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gradient-to-r from-red-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-8 h-8 text-red-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    Advanced Security
                  </h3>
                  <p className="text-slate-600 max-w-md mx-auto">
                    Next-generation security features to protect your data and transactions.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Shield className="w-5 h-5 text-green-600" />
                      <h4 className="font-medium text-slate-900">Zero-Trust Architecture</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Comprehensive security model that requires verification for every access request.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Cpu className="w-5 h-5 text-blue-600" />
                      <h4 className="font-medium text-slate-900">Blockchain Integration</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Immutable transaction records using distributed ledger technology.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Brain className="w-5 h-5 text-purple-600" />
                      <h4 className="font-medium text-slate-900">AI Threat Detection</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Machine learning-powered threat detection and response systems.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-3 mb-3">
                      <Globe className="w-5 h-5 text-orange-600" />
                      <h4 className="font-medium text-slate-900">Compliance Monitoring</h4>
                    </div>
                    <p className="text-sm text-slate-600">
                      Automated compliance checking and regulatory reporting.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default FutureSection;

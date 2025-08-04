'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'

interface SystemMetrics {
  timestamp: string
  cpu_percent: number
  memory_percent: number
  memory_available_gb: number
  disk_usage_percent: number
  disk_free_gb: number
  load_average: number[]
  uptime_hours: number
  process_count: number
  network_connections: number
}

interface APIHealthCheck {
  endpoint: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  response_time_ms: number
  status_code?: number
  error_message?: string
  timestamp: string
}

interface Alert {
  type: string
  severity: 'warning' | 'critical'
  message: string
  timestamp: string
}

interface MonitoringData {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  system: SystemMetrics
  api_health: APIHealthCheck[]
  ollama_health: APIHealthCheck
  alerts: Alert[]
  summary: {
    total_alerts: number
    critical_alerts: number
    healthy_apis: number
    total_apis: number
  }
}

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8001' 
  : 'http://38.242.229.78:8001'

export default function MonitoringPage() {
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data: monitoringData, isLoading, error, refetch } = useQuery<MonitoringData>({
    queryKey: ['monitoring'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/monitoring/health`)
      if (!response.ok) {
        throw new Error('Failed to fetch monitoring data')
      }
      return response.json()
    },
    refetchInterval: autoRefresh ? 30000 : false, // Refresh every 30 seconds
    retry: 3,
  })

  const formatUptime = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)} minutes`
    if (hours < 24) return `${Math.round(hours)} hours`
    return `${Math.round(hours / 24)} days`
  }

  const formatBytes = (gb: number) => {
    if (gb < 1) return `${Math.round(gb * 1024)} MB`
    return `${gb.toFixed(1)} GB`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100'
      case 'degraded': return 'text-yellow-600 bg-yellow-100'
      case 'unhealthy': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getProgressColor = (percentage: number) => {
    if (percentage < 60) return 'bg-green-500'
    if (percentage < 80) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'critical': return 'text-red-600 bg-red-50 border-red-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading monitoring data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-red-800 text-lg font-semibold mb-2">Monitoring Error</h2>
          <p className="text-red-600 mb-4">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Monitoring</h1>
          <p className="text-gray-600">Real-time monitoring of Autopicker platform</p>
        </div>
        <div className="flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="mr-2"
            />
            Auto-refresh (30s)
          </label>
          <button
            onClick={() => refetch()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Refresh Now
          </button>
        </div>
      </div>

      {/* Overall Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">Overall Status</h3>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(monitoringData?.status || 'unknown')}`}>
              {monitoringData?.status || 'Unknown'}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {monitoringData?.status === 'healthy' ? '🟢' : 
             monitoringData?.status === 'degraded' ? '🟡' : '🔴'} System
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Active Alerts</h3>
          <p className="text-2xl font-bold text-gray-900">
            {monitoringData?.summary.critical_alerts || 0}
          </p>
          <p className="text-sm text-gray-600">
            {monitoringData?.summary.total_alerts || 0} total alerts
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">API Health</h3>
          <p className="text-2xl font-bold text-gray-900">
            {monitoringData?.summary.healthy_apis || 0}/{monitoringData?.summary.total_apis || 0}
          </p>
          <p className="text-sm text-gray-600">Healthy endpoints</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Uptime</h3>
          <p className="text-2xl font-bold text-gray-900">
            {monitoringData?.system ? formatUptime(monitoringData.system.uptime_hours) : 'N/A'}
          </p>
          <p className="text-sm text-gray-600">System uptime</p>
        </div>
      </div>

      {/* System Metrics */}
      {monitoringData?.system && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">System Resources</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* CPU Usage */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">CPU Usage</span>
                <span className="text-sm text-gray-600">{monitoringData.system.cpu_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${getProgressColor(monitoringData.system.cpu_percent)}`}
                  style={{ width: `${monitoringData.system.cpu_percent}%` }}
                ></div>
              </div>
            </div>

            {/* Memory Usage */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Memory Usage</span>
                <span className="text-sm text-gray-600">
                  {monitoringData.system.memory_percent.toFixed(1)}% ({formatBytes(monitoringData.system.memory_available_gb)} free)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${getProgressColor(monitoringData.system.memory_percent)}`}
                  style={{ width: `${monitoringData.system.memory_percent}%` }}
                ></div>
              </div>
            </div>

            {/* Disk Usage */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Disk Usage</span>
                <span className="text-sm text-gray-600">
                  {monitoringData.system.disk_usage_percent.toFixed(1)}% ({formatBytes(monitoringData.system.disk_free_gb)} free)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${getProgressColor(monitoringData.system.disk_usage_percent)}`}
                  style={{ width: `${monitoringData.system.disk_usage_percent}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Additional System Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200">
            <div>
              <p className="text-sm text-gray-500">Load Average</p>
              <p className="text-lg font-semibold">{monitoringData.system.load_average[0]?.toFixed(2) || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Processes</p>
              <p className="text-lg font-semibold">{monitoringData.system.process_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Network Connections</p>
              <p className="text-lg font-semibold">{monitoringData.system.network_connections}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Last Updated</p>
              <p className="text-lg font-semibold">
                {new Date(monitoringData.system.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* API Health Status */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">API Health Status</h2>
        
        <div className="space-y-4">
          {/* Ollama Health */}
          {monitoringData?.ollama_health && (
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center">
                <span className={`w-3 h-3 rounded-full mr-3 ${
                  monitoringData.ollama_health.status === 'healthy' ? 'bg-green-500' :
                  monitoringData.ollama_health.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></span>
                <div>
                  <p className="font-medium">Ollama Service</p>
                  <p className="text-sm text-gray-600">{monitoringData.ollama_health.endpoint}</p>
                </div>
              </div>
              <div className="text-right">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(monitoringData.ollama_health.status)}`}>
                  {monitoringData.ollama_health.status}
                </span>
                <p className="text-sm text-gray-600 mt-1">
                  {monitoringData.ollama_health.response_time_ms.toFixed(0)}ms
                </p>
              </div>
            </div>
          )}

          {/* API Endpoints */}
          {monitoringData?.api_health?.map((endpoint, index) => (
            <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center">
                <span className={`w-3 h-3 rounded-full mr-3 ${
                  endpoint.status === 'healthy' ? 'bg-green-500' :
                  endpoint.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></span>
                <div>
                  <p className="font-medium">{endpoint.endpoint}</p>
                  {endpoint.error_message && (
                    <p className="text-sm text-red-600">{endpoint.error_message}</p>
                  )}
                </div>
              </div>
              <div className="text-right">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(endpoint.status)}`}>
                  {endpoint.status}
                </span>
                <p className="text-sm text-gray-600 mt-1">
                  {endpoint.status_code ? `HTTP ${endpoint.status_code} • ` : ''}
                  {endpoint.response_time_ms.toFixed(0)}ms
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Alerts */}
      {monitoringData?.alerts && monitoringData.alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Active Alerts</h2>
          
          <div className="space-y-4">
            {monitoringData.alerts.map((alert, index) => (
              <div key={index} className={`p-4 border rounded-lg ${getSeverityColor(alert.severity)}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-lg mr-3">
                      {alert.severity === 'critical' ? '🚨' : '⚠️'}
                    </span>
                    <div>
                      <p className="font-medium capitalize">{alert.type.replace('_', ' ')}</p>
                      <p className="text-sm">{alert.message}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      alert.severity === 'critical' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {alert.severity}
                    </span>
                    <p className="text-sm text-gray-600 mt-1">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Alerts */}
      {monitoringData?.alerts && monitoringData.alerts.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center">
            <span className="text-2xl mr-3">✅</span>
            <div>
              <h3 className="text-green-800 font-semibold">All Systems Operational</h3>
              <p className="text-green-600">No active alerts detected</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
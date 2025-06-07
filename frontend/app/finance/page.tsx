"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAppContext } from "@/context/app-context";
import { Printer, FileDown } from "lucide-react";
import Markdown from "@/components/markdown";

const FinancePage = () => {
  const [reportType, setReportType] = useState("");
  const [timeDimension, setTimeDimension] = useState("");
  const [report, setReport] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const {
    state: { socket },
    sendMessage,
  } = useAppContext();

  useEffect(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      sendMessage({
        type: "init_agent",
        content: {
          model_name: "claude-3-7-sonnet@20250219",
          tool_args: {
            thinking_tokens: false,
          },
        },
      });
    }
  }, [socket, sendMessage]);

  const handleGenerateReport = async () => {
    if (!reportType || !timeDimension) {
      alert("请选择财务报告类型和时间以生成报告");
      return;
    }
    setIsLoading(true);
    setReport("");

    sendMessage({
      type: "query",
      content: {
        text: `Generate a ${reportType} for ${timeDimension}`,
        tool_choice: {
          type: "tool",
          name: "generate_report",
          input: {
            report_type: reportType,
            time_dimension: timeDimension,
            department: "finance",
          },
        },
      },
    });
  };

  return (
    <div className="container mx-auto p-4 h-full flex flex-col">
      <h1 className="text-2xl font-bold mb-4">分析数据</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <Select onValueChange={setReportType}>
          <SelectTrigger>
            <SelectValue placeholder="财务分析类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="balance_sheet">资产负债表</SelectItem>
            <SelectItem value="income_statement">利润表</SelectItem>
            <SelectItem value="cash_flow_statement">现金流量表</SelectItem>
          </SelectContent>
        </Select>
        <Select onValueChange={setTimeDimension}>
          <SelectTrigger>
            <SelectValue placeholder="时间" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="2024-Q2">2024年第二季度</SelectItem>
            <SelectItem value="2024-Q1">2024年第一季度</SelectItem>
            <SelectItem value="2023">2023年年度</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={handleGenerateReport} disabled={isLoading}>
          {isLoading ? "生成中..." : "生成报告"}
        </Button>
      </div>
      <div className="flex-grow mt-4">
        <Card className="h-full">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>即将生成报告...</CardTitle>
            <div className="flex space-x-2">
              <Button variant="outline" size="icon" disabled={!report || isLoading}>
                <Printer className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" disabled={!report || isLoading}>
                <FileDown className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="h-full overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <p>正在生成报告...</p>
              </div>
            ) : report ? (
              <Markdown>{report}</Markdown>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <p>请选择财务报告类型和时间以生成报告</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FinancePage;

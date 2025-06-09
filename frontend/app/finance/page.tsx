"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAppContext } from "@/context/app-context";
import { Printer, FileDown } from "lucide-react";
import Markdown from "@/components/markdown";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const FinancePage = () => {
  const [reportType, setReportType] = useState("");
  const [timeDimension, setTimeDimension] = useState("");
  const [report, setReport] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const {
    state: { socket, agent, currentModel },
    sendMessage,
  } = useAppContext();
  const reportRef = useRef(null);

  useEffect(() => {
    if (socket && socket.readyState === WebSocket.OPEN && !agent) {
      sendMessage({
        type: "init_agent",
        content: {
          model_name: currentModel,
          tool_args: {
            thinking_tokens: false,
          },
        },
      });
    }
  }, [socket, agent, currentModel, sendMessage]);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      if (data.type === "report_generated") {
        setReport(data.content);
        setIsLoading(false);
      }
    };
    socket?.addEventListener("message", handleMessage);
    return () => {
      socket?.removeEventListener("message", handleMessage);
    };
  }, [socket]);

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
          name: "report_generator",
          input: {
            report_type: reportType,
            time_dimension: timeDimension,
            department: "finance",
          },
        },
      },
    });
  };

  const handlePrint = () => {
    const printContent = reportRef.current;
    if (printContent) {
      const printWindow = window.open("", "_blank");
      printWindow?.document.write(
        "<html><head><title>Print Report</title></head><body>"
      );
      printWindow?.document.write((printContent as any).innerHTML);
      printWindow?.document.write("</body></html>");
      printWindow?.document.close();
      printWindow?.print();
    }
  };

  const handleDownloadPdf = () => {
    const input = reportRef.current;
    if (input) {
      html2canvas(input).then((canvas) => {
        const imgData = canvas.toDataURL("image/png");
        const pdf = new jsPDF();
        const imgProps = pdf.getImageProperties(imgData);
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
        pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
        pdf.save("report.pdf");
      });
    }
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
              <Button
                variant="outline"
                size="icon"
                onClick={handlePrint}
                disabled={!report || isLoading}
              >
                <Printer className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={handleDownloadPdf}
                disabled={!report || isLoading}
              >
                <FileDown className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="h-full overflow-y-auto" ref={reportRef}>
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

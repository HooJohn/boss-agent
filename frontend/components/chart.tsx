"use client";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ChartProps {
  data: any;
}

const Chart = ({ data }: ChartProps) => {
  const chartType = data.chart_type;

  const chartComponents: { [key: string]: React.ReactElement } = {
    bar: (
      <BarChart data={data.x_axis.data.map((x: any, i: number) => ({ x, y: data.y_axis.data[i] }))}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="x" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="y" fill="#8884d8" />
      </BarChart>
    ),
    line: (
      <LineChart data={data.x_axis.data.map((x: any, i: number) => ({ x, y: data.y_axis.data[i] }))}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="x" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="y" stroke="#8884d8" />
      </LineChart>
    ),
    pie: (
      <PieChart>
        <Pie
          data={data.x_axis.data.map((x: any, i: number) => ({ name: x, value: data.y_axis.data[i] }))}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={150}
          fill="#8884d8"
        />
        <Tooltip />
      </PieChart>
    ),
  };

  return (
    <div style={{ width: "100%", height: 400 }}>
      <ResponsiveContainer>
        {chartComponents[chartType] || <div>Unsupported chart type</div>}
      </ResponsiveContainer>
    </div>
  );
};

export default Chart;

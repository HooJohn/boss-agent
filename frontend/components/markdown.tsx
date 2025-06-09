"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import rehypeMathJax from "rehype-mathjax";
import rehypeKatex from "rehype-katex";
import Chart from "./chart";

import "katex/dist/katex.min.css";

interface MarkdownProps {
  children: string | null | undefined;
}

const Markdown = ({ children }: MarkdownProps) => {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, rehypeHighlight, remarkMath]}
        rehypePlugins={[rehypeRaw, rehypeMathJax, rehypeKatex]}
        components={{
          a: ({ ...props }) => (
            <a target="_blank" rel="noopener noreferrer" {...props} />
          ),
          code({ node, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const inline = node?.properties?.inline as boolean | undefined;
            if (!inline && match && match[1] === "json") {
              try {
                const json = JSON.parse(String(children).replace(/\n$/, ""));
                if (json.visualization) {
                  return <Chart data={json.visualization} />;
                }
              } catch (error) {
                // Not a valid JSON, render as a code block
              }
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
};

export default Markdown;

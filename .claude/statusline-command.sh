#!/bin/bash
input=$(cat)
model=$(echo "$input" | jq -r '.model.display_name // .model.id // "unknown"')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
current=$(echo "$input" | jq -r '.context_window.current_usage // empty')
window_size=$(echo "$input" | jq -r '.context_window.context_window_size // empty')

context_info=""
if [ -n "$current" ] && [ "$current" != "null" ]; then
  input_tok=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
  output_tok=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // 0')
  total_current=$((input_tok + output_tok))
  if [ -n "$window_size" ] && [ "$window_size" != "null" ]; then
    used_k=$((total_current / 1000))
    total_k=$((window_size / 1000))
    if [ -n "$used_pct" ] && [ "$used_pct" != "null" ]; then
      context_info="Context: ${used_k}k/${total_k}k ($(printf '%.0f' "$used_pct")%)"
    else
      context_info="Context: ${used_k}k/${total_k}k"
    fi
  fi
elif [ -n "$used_pct" ] && [ "$used_pct" != "null" ]; then
  context_info="Context: $(printf '%.0f' "$used_pct")%"
fi

printf "%s" "$model"
[ -n "$context_info" ] && printf " | %s" "$context_info"
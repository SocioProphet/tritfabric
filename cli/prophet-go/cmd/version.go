package cmd

import (
  "fmt"

  "github.com/spf13/cobra"
)

var versionCmd = &cobra.Command{
  Use:   "version",
  Short: "Print version",
  Run: func(cmd *cobra.Command, args []string) {
    fmt.Println("prophet-go 0.1.0")
  },
}

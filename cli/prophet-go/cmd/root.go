package cmd

import (
  "fmt"
  "os"

  "github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
  Use:   "prophet",
  Short: "Prophet CLI (training/customization side)",
  Long:  "Prophet CLI scaffolding. Wire this to SocioProphet training platform APIs.",
}

func Execute() {
  if err := rootCmd.Execute(); err != nil {
    fmt.Fprintln(os.Stderr, err)
    os.Exit(1)
  }
}

func init() {
  rootCmd.AddCommand(versionCmd)
}

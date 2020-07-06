package main

import "testing"

func TestConvertMonicaToMet(t *testing.T) {
	type args struct {
		folderIn  string
		folderOut string
		project   string
		seperator string
		co2       int
	}
	tests := []struct {
		name    string
		args    args
		wantErr bool
	}{
		// TODO: Add test cases.
		{"historical", args{"../climate-data/corrected/0/0_0", "../climate-data/met/0/0_0", "..", ",", 499}, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if err := ConvertMonicaToMet(tt.args.folderIn, tt.args.folderOut, tt.args.project, tt.args.seperator, tt.args.co2); (err != nil) != tt.wantErr {
				t.Errorf("ConvertMonicaToMet() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

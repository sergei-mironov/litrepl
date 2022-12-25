{
  description = "LitREPL developement environment";

  nixConfig = {
    bash-prompt = "\[LitREPL-develop\]$ ";
  };

  # inputs.nixpkgs.url = "github:grwlf/nixpkgs/local13";
  inputs = {
    # nixpkgs.url = "path:/home/grwlf/proj/nixcfg/nixpkgs";
    # nixpkgs.url = "nixpkgs";
    nixpkgs.url = "github:grwlf/nixpkgs/local13";
  };

  outputs = { self, nixpkgs }:
    let
      # Generate a user-friendly version number.
      version = builtins.substring 0 8 self.lastModifiedDate;

      # System types to support.
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];

      # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

      # Nixpkgs instantiated for supported system types.
      nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; });
    in {

      packages = forAllSystems (system:
        let pkgs = nixpkgsFor.${system};
        in (import ./default.nix) {inherit pkgs; src = self;});

      devShells = forAllSystems (system:
        let pkgs = nixpkgsFor.${system};
        in {
          default = ((import ./default.nix) {inherit pkgs; src = self;}).shell;
        });
    };

}

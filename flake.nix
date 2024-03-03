{
  description = "LitREPL developement environment";

  nixConfig = {
    bash-prompt = "\[LitREPL-develop\]$ ";
  };

  inputs = {
    # nixpkgs.url = "path:/home/grwlf/proj/nixcfg/nixpkgs";
    # nixpkgs.url = "nixpkgs";
    # nixpkgs.url = "github:grwlf/nixpkgs/local13";
    # nixpkgs.url = "github:grwlf/nixpkgs/local14";
    nixpkgs = {
      url = "github:grwlf/nixpkgs/local15";
    };
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

      defaultsFor = system : (import ./default.nix) {
        pkgs = nixpkgsFor.${system};
        src = self;
        revision = if self ? rev then self.rev else null;
      };
    in {
      packages = forAllSystems defaultsFor;

      devShells = forAllSystems (system: (let
        outputs = defaultsFor system;
      in outputs // { default = outputs.shell; }));
    };

}

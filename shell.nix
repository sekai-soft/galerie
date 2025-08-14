{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.virtualenv
  ];

  shellHook = ''
    if [ ! -d "venv" ]; then
      python -m venv venv
    fi
    source venv/bin/activate

    if [ -f "requirements.txt" ]; then
      pip install -r requirements.txt
    fi
  '';
}

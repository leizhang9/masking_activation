library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package boolean_to_arithmetic_sni_pkg is

	component boolean_to_arithmetic_sni is
		generic (
			L_g            : positive; -- fixed point width
			D_g            : positive -- number of share
		);
		port (
			b_share_i      : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
			rnd_i          : in  std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
			gamma_i        : in  std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
			clk_i          : in  std_ulogic;
			rst_i          : in  std_ulogic;
			a_share_o      : out std_ulogic_vector (L_g * D_g - 1 downto 0)
		);
	end component;

end package boolean_to_arithmetic_sni_pkg;

package body boolean_to_arithmetic_sni_pkg is

end package body;


library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
library work;
use work.prim_ops_pkg.all;

entity boolean_to_arithmetic_sni is
	generic (
		L_g            : positive := 4; -- fixed point width
		D_g            : positive := 2  -- number of shares
	);
	port (
		b_share_i      : in  std_logic_vector (L_g * D_g - 1 downto 0);
		rnd_i          : in  std_logic_vector (L_g * (D_g - 1) - 1 downto 0);
		gamma_i        : in  std_logic_vector (L_g * (D_g - 1) - 1 downto 0);
		clk_i          : in  std_logic;
		rst_i          : in  std_logic;
		a_share_o      : out std_logic_vector (L_g * D_g - 1 downto 0)
	);
end;

architecture rtl of boolean_to_arithmetic_sni is

	signal a_share_reg : std_logic_vector (L_g * D_g - 1 downto 0);
	signal a0          : std_logic_vector (L_g - 1 downto 0);
  signal a1          : std_logic_vector (L_g - 1 downto 0);
	signal a1_0        : std_logic_vector (L_g - 1 downto 0);
	signal a1_1        : std_logic_vector (L_g - 1 downto 0);
	signal gamma       : std_logic_vector (L_g - 1 downto 0);
	signal tau         : std_logic_vector (L_g - 1 downto 0);
	signal tau_0       : std_logic_vector (L_g - 1 downto 0);
	signal tau_1       : std_logic_vector (L_g - 1 downto 0);
	signal b0          : std_logic_vector (L_g - 1 downto 0);
	signal b1          : std_logic_vector (L_g - 1 downto 0);
	signal res         : std_logic_vector (L_g * D_g - 1 downto 0);

	attribute DONT_TOUCH : string;
	attribute keep : string;

	attribute keep of a_share_reg : signal is "true";
  attribute keep of a0          : signal is "true";
  attribute keep of a1_0        : signal is "true";
  attribute keep of a1_1        : signal is "true";
  attribute keep of a1          : signal is "true";
  attribute keep of gamma       : signal is "true";
  attribute keep of tau         : signal is "true";
  attribute keep of tau_0       : signal is "true";
  attribute keep of tau_1       : signal is "true";
  attribute keep of b0          : signal is "true";
  attribute keep of b1          : signal is "true";
  attribute keep of res         : signal is "true";


begin

	boolean_to_arithmetic_p : process(clk_i) is
    begin
		if (clk_i'event and clk_i = '1') then
            a_share_reg <= res;
		end if;
	end process boolean_to_arithmetic_p;

    b0 <= PXOR(b_share_i(L_g - 1 downto 0), rnd_i);
    b1 <= PXOR(b_share_i((2 * L_g) - 1 downto L_g), rnd_i);

    tau_0 <= PXOR(b1, gamma_i);
    tau_1 <= PADD(tau_0, twos_complement(gamma_i));
    tau <= PXOR(tau_1, b1);

    gamma <= PXOR(gamma_i, b0);
    a1_0 <= PXOR(b1, gamma);
    a1_1 <= PADD(a1_0, twos_complement(gamma));
    a1 <= PXOR(a1_1, tau);
    a0 <= b0;

    res <= a1 & a0;

	a_share_o <= a_share_reg;

end rtl;

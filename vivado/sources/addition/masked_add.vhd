library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package masked_add_pkg is

	component masked_add is
		generic (
			L_g            : positive; -- fixed point width
			D_g            : positive; -- number of shares
			sni_g          : boolean := false;
			sub_g          : boolean := false -- true: c = a + b; false: c = a - b
		);
		port (
			clk_i					 : in  std_ulogic;
			rst_i					 : in  std_ulogic;
			a_i            : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
			b_i            : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
			rnd_i          : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
			c_o            : out std_ulogic_vector (L_g * D_g - 1 downto 0)
		);
	end component;

end package masked_add_pkg;

package body masked_add_pkg is

end package body;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;

entity masked_add is
	generic (
		L_g            : positive; -- fixed point width
		D_g            : positive; -- number of shares
		sni_g          : boolean := false;
		sub_g          : boolean := false -- true: c = a + b; false: c = a - b
	);
	port (
		clk_i					 : in  std_ulogic;
		rst_i					 : in  std_ulogic;
		a_i            : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		b_i            : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		rnd_i          : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		c_o            : out std_ulogic_vector (L_g * D_g - 1 downto 0)
	);
end masked_add;

architecture rtl of masked_add is

	signal a0 		: std_ulogic_vector(L_g - 1 downto 0);
	signal a1 		: std_ulogic_vector(L_g - 1 downto 0);
	signal b0 		: std_ulogic_vector(L_g - 1 downto 0);
	signal b1 		: std_ulogic_vector(L_g - 1 downto 0);
	signal c0 		: std_ulogic_vector(L_g - 1 downto 0);
	signal c1 		: std_ulogic_vector(L_g - 1 downto 0);
	signal r0 		: std_ulogic_vector(L_g - 1 downto 0);
	signal r1 		: std_ulogic_vector(L_g - 1 downto 0);


	signal a0_reg : std_ulogic_vector(L_g - 1 downto 0);
	signal a1_reg : std_ulogic_vector(L_g - 1 downto 0);
	signal b0_reg : std_ulogic_vector(L_g - 1 downto 0);
	signal b1_reg : std_ulogic_vector(L_g - 1 downto 0);

	attribute DONT_TOUCH : string;
	attribute keep : string;

	attribute keep of b0_reg : signal is "true";
	attribute keep of b1_reg : signal is "true";
	attribute keep of c0		 : signal is "true";
	attribute keep of c1		 : signal is "true";
	attribute keep of a0_reg : signal is "true";
	attribute keep of a1_reg : signal is "true";
	attribute keep of a0 		 : signal is "true";
	attribute keep of a1     : signal is "true";
	attribute keep of b0 		 : signal is "true";
	attribute keep of b1     : signal is "true";
	attribute keep of r0 		 : signal is "true";
	attribute keep of r1     : signal is "true";

begin

 	sub : if sub_g = true generate
		c0 <= std_ulogic_vector(unsigned(a0_reg) + unsigned(not b0_reg) + 1);
		c1 <= std_ulogic_vector(unsigned(a1_reg) + unsigned(not b1_reg) + 1);
 	end generate;

	add : if sub_g = false generate
		c0 <= std_ulogic_vector(unsigned(a0_reg) + unsigned(b0_reg));
		c1 <= std_ulogic_vector(unsigned(a1_reg) + unsigned(b1_reg));
	end generate;


	reg : process(clk_i)
	begin
		if clk_i'event and clk_i = '1' then
			if rst_i = '1' then
				b0_reg <= (others => '0');
				b1_reg <= (others => '0');
				a0_reg <= (others => '0');
				a1_reg <= (others => '0');
				a0 <= (others => '0');
				a1 <= (others => '0');
				b0 <= (others => '0');
				b1 <= (others => '0');
				r0 <= (others => '0');
				r1 <= (others => '0');
			else
				b0_reg <= std_ulogic_vector(unsigned(b0) + unsigned(r1));
				b1_reg <= std_ulogic_vector(unsigned(b1) - unsigned(r1));
				a0_reg <= std_ulogic_vector(unsigned(a0) + unsigned(r0));
				a1_reg <= std_ulogic_vector(unsigned(a1) - unsigned(r0));
				a0 <= a_i(L_g * D_g - 1 downto L_g);
				a1 <= a_i(L_g - 1 downto 0);
				b0 <= b_i(L_g * D_g - 1 downto L_g);
				b1 <= b_i(L_g - 1 downto 0);
				r0 <= rnd_i(L_g * D_g - 1 downto L_g);
				r1 <= rnd_i(L_g - 1 downto 0);
			end if;
		end if;
	end process;

	c_o <= c0 & c1;

end rtl;

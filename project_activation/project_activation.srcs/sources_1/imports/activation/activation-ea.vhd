-- activation component latency: xxx clock cycles
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;

use work.mask_util_pkg.all;
use work.prim_ops_pkg.all;

entity activation is
	generic (
		L_g                  : positive := 32; -- fixed point width
		D_g                  : positive := 2; -- number of shares
		fp_fractional_bits_g : positive := 6
	);
	port (
		clk_i       : in  std_ulogic;
		rst_i       : in  std_ulogic;
		start_i			: in 	std_ulogic;
		share_i     : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		rnd_i       : in  std_ulogic_vector (19 * L_g * (D_g - 1) - 1 downto 0);
		done_o			: out std_ulogic;
		share_o     : out std_ulogic_vector (L_g * D_g - 1 downto 0)
--		trn_share_o : out std_ulogic_vector (L_g * D_g - 1 downto 0)
	);
end activation;


architecture rtl of activation is

--	constant zero_c : std_ulogic_vector (L_g * D_g - 1 downto 0) := (others => '0');

--	signal sign_s       : std_ulogic_vector (L_g * D_g - 1 downto 0);
--	signal sign_n_s     : std_ulogic_vector (L_g * D_g - 1 downto 0);

--	signal trn_s     : std_ulogic_vector (L_g * D_g - 1 downto 0);

--	signal activation_s : std_ulogic_vector (L_g * D_g - 1 downto 0);

--	signal rnd_mul_shift_reg : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
--	signal rnd_mul_s : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);

--	signal trn_share_shift_reg : std_ulogic_vector (L_g * D_g - 1 downto 0);

	attribute DONT_TOUCH : string;
	attribute keep : string;

--	attribute DONT_TOUCH of cmp_inst		: label is "true";
    attribute DONT_TOUCH of f_activation_inst		: label is "true";
--	attribute DONT_TOUCH of mul_inst		: label is "true";

--	attribute keep of sign_s            : signal is "true";
--	attribute keep of sign_n_s          : signal is "true";
--	attribute keep of activation_s      : signal is "true";
--	attribute keep of rnd_mul_shift_reg : signal is "true";

begin

--	rnd_mul_s <= rnd_i(19 * L_g * (D_g - 1) - 1 downto 18 * L_g * (D_g - 1));

--	process(clk_i)
--	begin
--		if (rising_edge(clk_i)) then
--			if (rst_i = '1') then
--				rnd_mul_shift_reg <= (others => '0');
--				trn_share_shift_reg <= (others => '0');

--			else
--				rnd_mul_shift_reg <= rnd_mul_s;
--				trn_share_shift_reg <= trn_s;

--			end if;
--		end if;
--	end process;

--	cmp_inst : entity work.masked_cmp_trn
--	generic map (
--		L_g                  => L_g,
--		D_g                  => D_g,
--		fp_fractional_bits_g => fp_fractional_bits_g
--	)
--	port map (
--		clk_i       => clk_i,
--		rst_i       => rst_i,
--		a_i         => share_i,
--		b_i         => zero_c,
--		rnd_i       => rnd_i(18 * L_g * (D_g - 1) - 1 downto 0),
--		start_i			=> std_logic(start_i),
--		done_o			=> done_o,
--		c_o         => sign_s,
--		d_o         => sign_n_s,
--		trn_o       => trn_s
--	);

    f_activation_inst : entity work.masked_exponential
	port map (
		clk       => clk_i,
		reset     => rst_i,
		x1        => share_i(L_g * D_g - 1 downto L_g),
		rnd       => share_i(L_g - 1 downto 0),
		r0        => "0000000000"&rnd_i(18 * L_g - 1-10 downto 17 * L_g),
		r1        => "0000000000"&rnd_i(17 * L_g - 1-10 downto 16 * L_g),
		r2        => "0000000000"&rnd_i(16 * L_g - 1-10 downto 15 * L_g),
		done_o    => done_o,
		output    => share_o
	);

--	mul_inst : entity work.masked_mul
--	generic map (
--		L_g   => L_g,
--		D_g   => D_g
--	)
--	port map (
--		rnd_i => rnd_mul_shift_reg,
--		clk_i => clk_i,
--		rst_i => rst_i,
--		a_i   => sign_s,
--		b_i   => trn_s,
--		c_o   => activation_s
--	);

--	share_o <= activation_s;
--	trn_share_o <= trn_share_shift_reg;

end rtl;

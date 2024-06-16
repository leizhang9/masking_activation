library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
USE ieee.math_real.log2;
USE ieee.math_real.ceil;
USE ieee.math_real.uniform;

library work;
use work.prim_ops_pkg.all;
use work.mask_util_pkg.all;

entity masked_mul_tb is
end masked_mul_tb;

architecture rtl of masked_mul_tb is

	constant clk_freq_c   : positive := 100000000;
	constant clk_period_c : time := ((1000000000/clk_freq_c)) * 1 ns;
	constant L_c          : positive := 32; 
	constant D_c          : positive := 2;
	constant fp_fractional_bits_c : positive := 6;

	constant pipeline_latency_c : integer := integer(ceil(log2(real((2 + 1))))) + 3; -- plus 3 to account for multiplier latency

	signal clk_s     : std_ulogic := '0';
	signal rst_s     : std_ulogic;
	
	signal rnd_s       : std_ulogic_vector (L_c - 1 downto 0);
	signal rnd_trunc_s : std_ulogic_vector (L_c - 1 downto 0);

	signal a_s       : std_ulogic_vector (L_c * D_c - 1 downto 0);
	signal b_s       : std_ulogic_vector (L_c * D_c - 1 downto 0);
	signal c_s       : std_ulogic_vector (L_c * D_c - 1 downto 0);

	signal result      : std_ulogic_vector (L_c - 1 downto 0);
	signal result_real : real;

	signal trunc_shares_s : std_ulogic_vector (L_c * D_c - 1 downto 0);

	component masked_mul is
		generic (
			L_g           : positive := 32; -- fixed point width
			D_g           : positive := 2 -- number of shares
		);
		port (
			rnd_i      : in  std_ulogic_vector(L_g * (D_g - 1) - 1 downto 0);
			clk_i      : in  std_ulogic;
			rst_i      : in  std_ulogic;
			a_i        : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
			b_i        : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
			c_o        : out std_ulogic_vector (L_g * D_g - 1 downto 0)
		);
	end component;


begin

	clk_s <= not clk_s after ((1000000000/clk_freq_c)/2) * 1 ns;
	
	dut : masked_mul
	generic map (
		L_g   => L_c,
		D_g   => D_c
	) 
	port map (
		rnd_i => rnd_s,
		clk_i => clk_s,
		rst_i => rst_s,
		a_i   => a_s,
		b_i   => b_s,
		c_o   => c_s
	);

	trunc : entity work.masked_trunc
	generic map (
		L_g                   => L_c,
		D_g                   => D_c,
		fp_fractional_bits_g  => fp_fractional_bits_c
	) port map (
		shares_i        => c_s,
		rnd_i           => rnd_trunc_s,
		trunc_shares_o  => trunc_shares_s
	);

	result <= PADD(trunc_shares_s(L_c - 1 downto 0), trunc_shares_s(2*L_c - 1 downto L_c));
	result_real <= convert_fp_to_real(result);

	process 
		
		variable seed1, seed2 : integer := 999;

		impure function rand_slv(len : integer) return std_logic_vector is
			variable r : real;
			variable slv : std_logic_vector(len - 1 downto 0);
		begin
			for i in slv'range loop
				uniform(seed1, seed2, r);
				slv(i) := '1' when r > 0.5 else '0';
			end loop;
			return slv;
		end function;

		variable a  : real := 1.0;
		variable b  : real := 359.0;

		variable a_v : std_ulogic_vector (L_c * D_c - 1 downto 0);
		variable b_v : std_ulogic_vector (L_c * D_c - 1 downto 0);

	begin
		
		
		a_v(L_c * D_c - 1 downto 0) := 
			mask_val(
				convert_real_to_fp(a),
				rand_slv(L_c)					
			);
		b_v(L_c * D_c - 1 downto 0) := 
			mask_val(
				convert_real_to_fp(b),
				rand_slv(L_c)
			);
		

		rst_s <= '0';

		wait until falling_edge(clk_s);
		report "Reset";
		rst_s <= '1';
		wait until falling_edge(clk_s);
		rst_s <= '0';

		rnd_s <= rand_slv(L_c);
		rnd_trunc_s <= rand_slv(L_c);

		a_s <= a_v;
		b_s <= b_v;

		for i in 0 to pipeline_latency_c loop
			wait until falling_edge(clk_s);
		end loop;

		wait for 1 ns;
						
		report "SIMULATION FINSIHED" severity failure;
		wait;



	end process;




end rtl;